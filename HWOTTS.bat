@echo off
move input.txt binary
cd binary
tr.exe '\n\r' ' ' < input.txt > input1.txt
voicetext_paul.exe
sox.exe -q output.wav -r 44100 -b 16 -c 1 HWO.wav
del output.wav
move HWO.wav ..
del input1.txt
del input.txt
