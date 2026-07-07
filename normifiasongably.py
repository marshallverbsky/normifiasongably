from os.path import dirname, realpath
from argparse import ArgumentParser
from pydub import AudioSegment
from sys import stderr
from json import dumps
import ffmpeg, os, json, re, math, shutil

audioexts = ('.mp3', '.wav', '.m4a')
triagedir = '/home/user/example/triage'
musicdir = '/home/user/example/music'

###define function for formatting the loudnorm output###
def parse_loudnorm_output(output_lines):
    loudnorm_start = False
    loudnorm_end = False
    for index, line in enumerate(output_lines):
        if line.startswith("[Parsed_loudnorm"):
            loudnorm_start = index + 1
            continue
        if loudnorm_start and line.startswith("}"):
            loudnorm_end = index + 1
            break

    loudnorm_format = "\n".join(output_lines[loudnorm_start:loudnorm_end])

    loudnorm_stats = json.loads(loudnorm_format)

    return loudnorm_stats

###move through folders###
for root, dirs, files in os.walk(triagedir):
    lufssum = 0
    filetotal = 0
    tpbase = -99
    for name in files:
        if name.endswith(audioexts):
	###measure loudness of each file in a folder###
            audio = os.path.join(root, name)
            out, err = (
            ffmpeg
            .input(audio)
            .filter('loudnorm', print_format='json')
            .output('pipe:', format='null')
            .run(capture_stdout=True, capture_stderr=True)
            )
            lnres = (str(err))
            lnresparse = lnres.replace('\\n', '\n').replace('\\t', '\t')
            lnreslines = lnresparse.splitlines()
            levels = parse_loudnorm_output(lnreslines)
            lufs = float(levels.get("input_i"))
            lufssum += lufs
            filetotal += 1
            tpcomp = float(levels.get("input_tp"))
            if (tpcomp > tpbase):
                tpbase = tpcomp
            print(name, lufs, tpcomp, tpbase)
    if filetotal:
    ###average the measurements per folder###
        avglufs = round((lufssum / filetotal), 2)
        maxpeak = tpbase
        print(f"average lufs: {avglufs}, max true peak {maxpeak}")
        lufsref = -14
        lufsdiff = round(avglufs - lufsref, 2)
        peakref = -0.3
        peakdiff = round(maxpeak - peakref, 2)
#        print(avglufs, lufsref, lufsdiff, maxpeak, peakref, peakdiff)
        if (lufsdiff > 0.5):
	###if it's too loud, lower it###
            for i, name in enumerate(files):
                if name.endswith(audioexts):
                    print(f"{name} will be lowered by {-(lufsdiff)}db")
                    relpath = os.path.relpath(root, start=triagedir)
                    checkpath = os.path.join(musicdir, relpath)
                    if not os.path.exists(checkpath):
                        os.makedirs(checkpath)
                    prenorm = os.path.join(root, name)
                    pathpath = os.path.join(relpath, name)
                    newpath = os.path.join(musicdir, pathpath)
                    postnorm = os.path.splitext(newpath)[0]+'.mp3'
#                    print(relpath, "\n", prenorm, "\n", pathpath, "\n", newpath, "\n", postnorm, "\n", "\n")
                    tempname = f'temp{i}.mp3'
                    (
                    ffmpeg
                    .input(prenorm)
                    .filter('volume', volume=f"{-(lufsdiff)}dB")
                    .output(tempname, **{'map': '0:a', 'map': '0:v?', 'q:a': 0}, loglevel="quiet")
                    .run()
                    )
                    os.remove(prenorm)
                    shutil.move(tempname, postnorm)
        elif (lufsdiff < -0.5):
	###if it's too quiet, raise it, but only if it doesn't clip first###
            if (peakdiff >= 0):
                for i, name in enumerate(files):
                    if name.endswith(audioexts):
                        print(f"no change, {name} at {avglufs}lufs can't be raised without clipping")
                        relpath = os.path.relpath(root, start=triagedir)
                        checkpath = os.path.join(musicdir, relpath)
                        if not os.path.exists(checkpath):
                            os.makedirs(checkpath)
                        prenorm = os.path.join(root, name)
                        pathpath = os.path.join(relpath, name)
                        newpath = os.path.join(musicdir, pathpath)
                        postnorm = os.path.splitext(newpath)[0]+'.mp3'
#                        print(relpath, "\n", prenorm, "\n", newpath, "\n", postnorm, "\n", "\n")
                        tempname = f'temp{i}.mp3'
                        (
                        ffmpeg
                        .input(prenorm)
                        .output(tempname, **{'q:a': 0}, loglevel="quiet")
                        .run()
                        )
                        os.remove(prenorm)
                        shutil.move(tempname, postnorm)                        
            elif (peakdiff < lufsdiff):
                for i, name in enumerate(files):
                    if name.endswith(audioexts):
                        print(f"{name} will be raised by {-(lufsdiff)}db")
                        relpath = os.path.relpath(root, start=triagedir)
                        checkpath = os.path.join(musicdir, relpath)
                        if not os.path.exists(checkpath):
                            os.makedirs(checkpath)
                        prenorm = os.path.join(root, name)
                        pathpath = os.path.join(relpath, name)
                        newpath = os.path.join(musicdir, pathpath)
                        postnorm = os.path.splitext(newpath)[0]+'.mp3'
#                        print(relpath, "\n", prenorm, "\n", newpath, "\n", postnorm, "\n", "\n")
                        tempname = f'temp{i}.mp3'
                        (
                        ffmpeg
                        .input(prenorm)
                        .filter('volume', volume=f"{-(lufsdiff)}dB")
                        .output(tempname, **{'map': '0:a', 'map': '0:v?', 'q:a': 0}, loglevel="quiet")
                        .run()
                        )
                        os.remove(prenorm)
                        shutil.move(tempname, postnorm)
            elif (peakdiff > lufsdiff):
                for i, name in enumerate(files):
                    if name.endswith(audioexts):
                        print(f"{name} will be raised only by {-(peakdiff)}db to avoid clipping")
                        relpath = os.path.relpath(root, start=triagedir)
                        checkpath = os.path.join(musicdir, relpath)
                        if not os.path.exists(checkpath):
                            os.makedirs(checkpath)
                        prenorm = os.path.join(root, name)
                        pathpath = os.path.join(relpath, name)
                        newpath = os.path.join(musicdir, pathpath)
                        postnorm = os.path.splitext(newpath)[0]+'.mp3'
#                        print(relpath, "\n", prenorm, "\n", newpath, "\n", postnorm, "\n", "\n")
                        tempname = f'temp{i}.mp3'
                        (
                        ffmpeg
                        .input(prenorm)
                        .filter('volume', volume=f"{-(peakdiff)}dB")
                        .output(tempname, **{'map': '0:a', 'map': '0:v?', 'q:a': 0}, loglevel="quiet")
                        .run()
                        )
                        os.remove(prenorm)
                        shutil.move(tempname, postnorm)
        else:
        ###if it's in range, just convert to mp3 and move###
            for i, name in enumerate(files):
                if name.endswith(audioexts):
                    print(f"no change, {name} at {avglufs}lufs within range")
                    relpath = os.path.relpath(root, start=triagedir)
                    checkpath = os.path.join(musicdir, relpath)
                    if not os.path.exists(checkpath):
                        os.makedirs(checkpath)
                    prenorm = os.path.join(root, name)
                    pathpath = os.path.join(relpath, name)
                    newpath = os.path.join(musicdir, pathpath)
                    postnorm = os.path.splitext(newpath)[0]+'.mp3'
#                    print(relpath, "\n", prenorm, "\n", newpath, "\n", postnorm, "\n", "\n")
                    tempname = f'temp{i}.mp3'
                    (
                    ffmpeg
                    .input(prenorm)
                    .output(tempname, **{'q:a': 0}, loglevel="quiet")
                    .run()
                    )
                    os.remove(prenorm)
                    shutil.move(tempname, postnorm)

###remove empty folders from triage###
for root, dirs, files in os.walk(triagedir, topdown=False):
    empty = True
    for i in os.scandir(root):
        empty = False
        break
    if empty:
        print(f"{root} is empty, removing")
        os.rmdir(root)

os.system("sudo chown -R user:user /home/user/example")
os.system("sudo chmod -R 777 /home/user/example")
