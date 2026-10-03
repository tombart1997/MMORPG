"""Offline runtime audio: original music/ambience plus CC0 Kenney foley.
NPC lines are rendered during authoring only (--voices), using edge-tts.
python tools/build_game_audio.py; game/.local/audio_env/Scripts/python tools/build_game_audio.py --voices
"""
from pathlib import Path
import json,re,math,subprocess,shutil,sys,asyncio,urllib.request
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'game/assets/audio';DEST.mkdir(parents=True,exist_ok=True)
FFMPEG='ffmpeg'
def encode(source,target,filters=None):
    args=[FFMPEG,'-y','-hide_banner','-loglevel','error','-i',str(source)]
    if filters:args+=['-af',filters]
    args+=['-c:a','libvorbis','-q:a','4',str(target)];subprocess.run(args,check=True)

async def voices():
    import edge_tts
    folder=DEST/'voices';folder.mkdir(exist_ok=True)
    voice_map={'warden':'en-GB-RyanNeural','mara':'en-GB-SoniaNeural','keeper':'en-US-JennyNeural','smith':'en-GB-ThomasNeural','weapons':'en-CA-LiamNeural','stablemaster':'en-US-GuyNeural','armorer':'en-US-AriaNeural','apothecary':'en-AU-ElsieNeural','artificer':'en-GB-LibbyNeural','ash_scout':'en-CA-ClaraNeural'}
    available={entry['ShortName'] for entry in await edge_tts.list_voices()}
    for npc,voice in list(voice_map.items()):
        if voice not in available:voice_map[npc]='en-GB-SoniaNeural' if npc in ['apothecary','artificer','armorer','ash_scout'] else 'en-GB-RyanNeural'
    sem=asyncio.Semaphore(2);lines=[]
    async def generate(npc,key,text,voice):
        dest=folder/(key+'.ogg')
        if not dest.exists():
            async with sem:
                temp=ROOT/'game/.local'/(key+'.mp3')
                for attempt in range(3):
                    try:await edge_tts.Communicate(text,voice,rate='-6%').save(str(temp));break
                    except Exception as exc:
                        print('VOICE_RETRY',key,voice,str(exc),flush=True)
                        if attempt==2:
                            voice='en-GB-SoniaNeural' if npc in ['mara','keeper','armorer','apothecary','artificer','ash_scout'] else 'en-GB-RyanNeural'
                            await edge_tts.Communicate(text,voice).save(str(temp));break
                        await asyncio.sleep(1)
                encode(temp,dest,'loudnorm=I=-18:TP=-3:LRA=8,afade=t=in:d=0.015')
        lines.append({'npc':npc,'key':key,'text':text,'voice':voice})
        print('VOICE',key,flush=True)
    tasks=[]
    for path in sorted((ROOT/'game/data/npcs').glob('*.tres')):
        data=path.read_text();match=re.search(r'^id = &"([^"]+)"',data,re.M)
        if not match:continue
        npc=match.group(1);texts=[json.loads('"'+s+'"') for s in re.findall(r'^text = "(.*)"$',data,re.M)]
        voice=voice_map.get(npc,'en-GB-RyanNeural')
        for i,text in enumerate(texts):tasks.append(generate(npc,npc+'_page'+str(i),text,voice))
        if texts:tasks.append(generate(npc,npc+'_greeting',texts[0].split('. ')[0]+'.',voice))
    await asyncio.gather(*tasks)
    (folder/'manifest.json').write_text(json.dumps(sorted(lines,key=lambda x:x['key']),indent=2))

def audio_assets():
    import numpy as np
    from scipy.signal import butter,sosfilt
    from scipy.io import wavfile
    sr=44100;rng=np.random.RandomState(1281)
    def write(name,data):
        data=np.asarray(data);peak=np.max(np.abs(data))
        if peak>.92:data=data*.92/peak
        temp=ROOT/'game/.local'/(name+'.wav');wavfile.write(str(temp),sr,(data*32767).astype(np.int16));encode(temp,DEST/(name+'.ogg'))
    def note(midi,duration,kind):
        count=int(duration*sr);t=np.arange(count)/sr;f=440*2**((midi-69)/12)
        if kind=='pluck':
            # Physical string loop, with resonant body partials and a finger attack.
            period=max(2,int(sr/f));seed=rng.uniform(-1,1,period);x=np.zeros(count)
            x[:period]=seed
            for j in range(period,count):x[j]=.497*(x[j-period]+x[j-period+1])
            x+=.10*np.sin(2*np.pi*f*t)*np.exp(-t*2.8)
            env=np.minimum(t/.008,1)*np.minimum((duration-t)/.1,1)
        elif kind=='flute':
            vibrato=.002*np.sin(2*np.pi*4.8*t)*np.minimum(t/1.2,1)
            phase=2*np.pi*f*(t+vibrato/(2*np.pi*4.8))
            x=.7*np.sin(phase)+.18*np.sin(phase*2)+.04*np.sin(phase*3)
            x+=sosfilt(butter(2,3500,fs=sr,output='sos'),rng.normal(0,.022,count))
            env=np.minimum(t/.18,1)*np.minimum((duration-t)/.22,1)
        else:
            x=np.zeros(count)
            for detune in [-.002,0,.0018]:
                phase=2*np.pi*f*(1+detune)*t+.012*np.sin(2*np.pi*5*t)
                for k in range(1,6):x+=np.sin(phase*k)/(k**1.5)*.19
            env=np.minimum(t/.8,1)*np.minimum((duration-t)/1,1)
        return x*env
    for region,scale in [('briarwood',[62,65,67,69,72]),('cinderfall',[48,51,53,55,58])]:
        beat=60/76;bars=16;length=bars*4*beat;music=np.zeros((int(length*sr),2))
        def add(midi,start,dur,kind,level,pan):
            x=note(midi,dur,kind)*level;start=int(start*sr)
            idx=(np.arange(len(x))+start)%len(music)
            music[idx,0]+=x*math.sqrt((1-pan)/2);music[idx,1]+=x*math.sqrt((1+pan)/2)
        chords=[0,3,1,2]
        phrase=[0,2,3,2,1,0,1,2,4,3,2,1,0,2,1,0]
        for bar in range(bars):
            base=bar*4*beat;root=scale[chords[(bar//2)%4]]
            add(root-12,base,4.7*beat,'bow',.10,0)
            add(root-5,base+.12,4.5*beat,'bow',.045,.3)
            for pulse in range(4):
                midi=scale[(bar+pulse*2)%5]+(12 if pulse%2 else 0)
                add(midi,base+(pulse+.03)*beat,2.2*beat,'pluck',.10 if region=='briarwood' else .055,(-.45 if pulse%2 else .4))
            if bar%4 in [0,1,3]:
                midi=scale[phrase[bar]]+12
                add(midi,base+.4*beat,2.5*beat,'flute',.085 if region=='briarwood' else .035,-.15)
                if bar%4==1:add(scale[phrase[(bar+1)%16]]+12,base+3*beat,1.4*beat,'flute',.05,-.1)
        # Circular early reflections maintain a seamless musical/room tail at the loop.
        dry=music.copy()
        for delay,gain in [(.13,.17),(.27,.12),(.43,.08),(.71,.055)]:music+=np.roll(dry,int(delay*sr),axis=0)[:,::-1]*gain
        write('music_'+region,music)
    n=sr*24;t=np.arange(n)/sr
    wind=sosfilt(butter(3,1100,fs=sr,output='sos'),rng.normal(0,.055,n))
    wind*=.55+.2*np.sin(t*.37)+.15*np.sin(t*.17)
    ambience=np.column_stack([wind,np.roll(wind,710)])
    for start in [2.4,6.7,11.3,17.2,20.7]:
        for gap in [0,.16,.34]:
            tt=np.arange(int(sr*.12))/sr
            chirp=np.sin(2*np.pi*(2200*tt+2800*tt**2))*np.sin(np.pi*tt/.12)**2*.026
            at=int((start+gap)*sr);ambience[at:at+len(chirp),0]+=chirp;ambience[at:at+len(chirp),1]+=chirp*.6
    write('ambience_briarwood',ambience)
    rumble=sosfilt(butter(3,270,fs=sr,output='sos'),rng.normal(0,.09,n))
    write('ambience_cinderfall',np.column_stack([rumble,np.roll(rumble,1400)]))
    rpg=ROOT/'game/.local/audio_sources/rpg/Audio';impact=ROOT/'game/.local/audio_sources/impact/Audio'
    sfx=DEST/'sfx';sfx.mkdir(exist_ok=True)
    source_map={'swing_0':rpg/'knifeSlice.ogg','swing_1':rpg/'knifeSlice2.ogg','hit_flesh':rpg/'chop.ogg','coins':rpg/'handleCoins.ogg','pickup':rpg/'handleSmallLeather.ogg','equip':rpg/'drawKnife2.ogg'}
    for i in range(3):
        source_map['step_'+str(i)]=impact/('footstep_grass_%03d.ogg'%i)
        source_map['hoof_'+str(i)]=impact/('impactWood_medium_%03d.ogg'%i)
        source_map['hit_metal_'+str(i)]=impact/('impactMetal_light_%03d.ogg'%i)
    for name,source in source_map.items():shutil.copyfile(source,sfx/(name+'.ogg'))
    horse=ROOT/'game/.local/audio_sources/horse_nicker_1217.mp3'
    if not horse.exists():urllib.request.urlretrieve('https://bigsoundbank.com/UPLOAD/mp3/1217.mp3',horse)
    encode(horse,sfx/'mount.ogg','loudnorm=I=-20:TP=-5:LRA=8,afade=t=in:d=0.015,afade=t=out:st=1.44:d=0.18')
    # Original elemental pulses: restrained attacks complement the recorded sword foley.
    for kind,freq in [('thunder',70),('fire',140),('spirit',430),('sun',620),('spin',220),('sprint',350)]:
        t=np.arange(int(sr*.55))/sr;noise=rng.normal(0,1,len(t));env=np.exp(-t*8)*np.minimum(t/.01,1)
        x=(.18*np.sin(2*np.pi*(freq*t-45*t*t))+.08*sosfilt(butter(2,2200,fs=sr,output='sos'),noise))*env
        if kind in ['spirit','sun']:x+=.12*np.sin(2*np.pi*freq*2*t)*np.exp(-t*5)
        write('skill_'+kind,np.column_stack([x,np.roll(x,130)]))
    credits='''Audio assets for Ironfield\n\nRecorded foley: Kenney RPG Audio and Impact Sounds, CC0.\nhttps://kenney.nl/assets/rpg-audio\nhttps://kenney.nl/assets/impact-sounds\nSee bundled license files.\n\nMusic: original Ironfield compositions generated by tools/build_game_audio.py.\nAmbience and elemental pulses: original procedural audio from the same authoring script.\nNPC voice recordings: synthetic voices generated from the project dialogue during authoring\nusing Microsoft Edge TTS through https://github.com/rany2/edge-tts .\nThese are synthetic voices, not recordings or impersonations of named actors.\nAll shipped audio plays offline; there is no runtime TTS or network dependency.\n'''
    credits+='\nHorse vocal: Little neighing call #6, Joseph SARDIN / BigSoundBank, CC0.\nhttps://bigsoundbank.com/little-neighing-call-6-s1217.html\nA real outdoor horse recording, normalized and faded for the mount cue.\n'
    (DEST/'CREDITS.txt').write_text(credits)
    shutil.copyfile(ROOT/'game/.local/audio_sources/rpg/License.txt',DEST/'Kenney_RPG_License.txt')
    shutil.copyfile(ROOT/'game/.local/audio_sources/impact/License.txt',DEST/'Kenney_Impact_License.txt')
    print('AUDIO_ASSETS_COMPLETE',flush=True)
if __name__=='__main__':
    if '--voices' in sys.argv:asyncio.run(voices())
    else:audio_assets()
