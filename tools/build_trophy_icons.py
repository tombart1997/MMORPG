"""Authored vector trophy icons. Rebuilds 35 item-specific SVGs and wires ItemData."""
from pathlib import Path
import re, hashlib
ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'game/assets/icons/trophies';DEST.mkdir(parents=True,exist_ok=True)
COLORS={'red_wolf':'ae482e','blue_wolf':'477fc0','grey_wolf':'777e84','meadow_wolf':'967651','thicket_wolf':'635844','frost_wolf':'e8edf1','dusk_stalker':'403d50','moonfang':'9ba9cc','bloodfang':'782e26','bristle_boar':'8e6744','ironhide_boar':'58616a','mire_boar':'66563e','blacktusk':'302c29','obsidian_boar':'342e3e','reed_spider':'937647','copper_spider':'b6763d','venom_spider':'718842','widow_spider':'a23445','silk_matron':'8f5178','slate_guardian':'647581','cairn_sentinel':'9c8970','cairn_colossus':'7c7267','ancient_warden':'a49674','cinder_wisp':'ef8136','grave_wisp':'83aeb2','storm_wisp':'8f9ddb','ash_bandit':'b45c38','road_bandit':'967651','hollow_raider':'7189a0','exile_captain':'87599f','young':'91a84e','grown':'776449','ironback':'626b59','moss_shard':'80a967','wakeglass':'ed9233'}
def art(key,title):
    color=COLORS.get(key,'80a967');n=int(hashlib.sha256(key.encode()).hexdigest()[:4],16)
    shapes=[]
    if 'Fang' in title:
        # Species-colored fur cuff, two different teeth, and an unmistakable canine shape.
        off=n%5
        shapes=[f'<path d="M12 23 L17 10 L23 16 L28 8 L32 15 L40 10 L46 22 L42 31 L18 32Z" fill="#{color}" stroke="#1f2427" stroke-width="2"/>',f'<path d="M19 24 Q27 24 31 30 Q32 43 {19+off} 55 Q24 41 19 24Z" fill="url(#ivory)" stroke="#594b3c" stroke-width="1.4"/>',f'<path d="M35 24 L44 24 Q53 36 38 {52-off} Q42 38 35 24Z" fill="url(#ivory)" stroke="#594b3c" stroke-width="1.4"/>','<path d="M20 19 L24 22 M32 18 L35 22 M39 17 L41 20" stroke="#dfd0b2" stroke-width="1.5"/>']
    elif 'Tusk' in title:
        bend=39+n%10
        shapes=[f'<path d="M16 13 L28 17 L26 27 Q25 {bend} 47 48 Q18 61 12 35Z" fill="url(#ivory)" stroke="#594b3c" stroke-width="2"/>',f'<path d="M13 13 L17 8 L21 12 L25 9 L28 17 L26 27 L12 23Z" fill="#{color}" stroke="#242326" stroke-width="1.5"/>','<path d="M20 31 Q20 42 35 49 M17 33 L22 34 M18 37 L23 38" fill="none" stroke="#b7a888" stroke-width="1.1"/>']
    elif 'Silk' in title:
        shapes=[f'<path d="M12 18 L23 9 L49 18 L54 32 L43 52 L19 50 L9 34Z" fill="#{color}" opacity=".7"/>','<path d="M13 19 L50 44 M14 43 L47 17 M31 11 L31 53 M9 31 L54 31 M22 18 L41 20 L46 32 L38 44 L22 42 L17 31Z M18 15 L47 15 L52 37 L32 51 L12 37Z" fill="none" stroke="#e7debf" stroke-width="1.5"/>',f'<ellipse cx="32" cy="32" rx="{7+n%4}" ry="12" fill="#{color}" stroke="#252128" stroke-width="2"/>','<path d="M21 28 L15 24 M21 34 L14 39 M42 28 L48 24 M42 35 L49 40" stroke="#24212a" stroke-width="2.5"/>','<circle cx="29" cy="27" r="2" fill="#efc279"/><circle cx="35" cy="27" r="2" fill="#efc279"/>']
    elif 'Core' in title:
        points='12,22 23,10 39,12 51,26 46,46 32,55 15,47 9,33'
        shapes=[f'<polygon points="{points}" fill="#{color}" stroke="#292931" stroke-width="2"/>','<path d="M23 10 L27 25 L9 33 M27 25 L46 46 M27 25 L39 12 M32 55 L29 41" fill="none" stroke="#d1c6ac" stroke-width="2"/>',f'<path d="M29 22 L40 29 L37 40 L27 43 L20 34Z" fill="#{["71c2a9","81aad1","d69f5f","b68ad2"][n%4]}" stroke="#e3d8b4" stroke-width="1.4"/>',f'<path d="M27 29 L34 {32+n%5} L29 38" fill="none" stroke="#faf0d7" stroke-width="2"/>']
    elif 'Essence' in title or key=='wakeglass':
        shapes=[f'<path d="M28 53 Q9 41 19 26 L29 14 L34 6 Q37 18 48 29 Q58 47 38 54Z" fill="#{color}" opacity=".3"/>',f'<path d="M28 49 Q14 37 29 27 Q25 20 34 12 Q34 27 43 31 Q50 45 34 51Z" fill="#{color}" stroke="#e4c892" stroke-width="1.4"/>','<path d="M30 45 Q22 36 33 31 Q42 40 34 46Z" fill="#fff0bd"/>','<path d="M18 50 L23 55 L42 55 L47 50 L43 47 L23 47Z" fill="#514548" stroke="#bd9a61" stroke-width="1.6"/>']
    elif 'Insignia' in title:
        shapes=[f'<path d="M19 37 L15 56 L28 51 L32 57 L39 51 L50 55 L44 36Z" fill="#{color}" stroke="#211f25" stroke-width="1.6"/>',f'<path d="M14 17 L32 7 L50 17 L47 35 L32 46 L17 35Z" fill="#{color}" stroke="#c7a363" stroke-width="3"/>','<path d="M21 30 L42 18 M23 19 L40 33" stroke="#e1d4b9" stroke-width="3"/>',f'<circle cx="32" cy="26" r="{4+n%4}" fill="#c7a363" stroke="#413329" stroke-width="1.5"/>']
    elif key=='young':
        shapes=['<path d="M12 46 Q10 20 35 19 Q49 41 25 53Z" fill="#668839" stroke="#a4ba6d" stroke-width="1.5"/>','<path d="M18 49 L36 22 M23 42 L16 30 M28 35 L38 35" stroke="#b3c875" fill="none"/>','<path d="M39 9 Q34 21 28 30 Q23 45 39 49 Q54 46 50 32Z" fill="url(#sap)" stroke="#e1b965" stroke-width="1.5"/>','<path d="M38 25 Q31 36 35 40" fill="none" stroke="#ffebac" stroke-width="3"/>']
    elif key=='grown':
        shapes=['<path d="M12 14 L29 8 L31 45 L17 54 L9 35Z" fill="#80613d" stroke="#c09d6d" stroke-width="1.4"/>','<path d="M32 15 L48 11 L54 40 L39 54 L30 41Z" fill="#634a35" stroke="#a88c62" stroke-width="1.4"/>','<path d="M19 16 L17 37 L23 32 L21 47 M40 19 L39 35 L46 29 L45 43" fill="none" stroke="#362e24" stroke-width="3"/>','<path d="M10 21 L17 16 L19 24 L13 32 M32 42 L38 34 L42 42 L38 47" fill="#71884a"/>']
    elif key=='ironback':
        shapes=['<path d="M14 18 L28 10 L45 16 L51 37 L40 53 L21 49 L11 35Z" fill="#5c6961" stroke="#bbb794" stroke-width="2"/>','<path d="M28 10 L29 28 L14 18 M29 28 L51 37 M29 28 L21 49 M29 28 L45 16 M21 49 L40 53" fill="none" stroke="#313b36" stroke-width="3"/>','<path d="M18 21 L23 20 L23 25 M35 34 L42 36 L39 40" fill="none" stroke="#91a676" stroke-width="2"/>']
    else:
        shapes=['<path d="M12 32 L27 9 L45 15 L53 37 L33 55 L14 47Z" fill="#598d65" stroke="#bbd39a" stroke-width="2"/>','<path d="M27 9 L24 35 L33 55 M24 35 L45 15 M24 35 L53 37" fill="none" stroke="#86b381" stroke-width="2"/>']
    return '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64"><title>'+title+'</title><defs><linearGradient id="ivory" x2=".8" y2="1"><stop stop-color="#f5eacb"/><stop offset=".5" stop-color="#daceac"/><stop offset="1" stop-color="#a99574"/></linearGradient><linearGradient id="sap" x2=".6" y2="1"><stop stop-color="#f1cc67"/><stop offset="1" stop-color="#c07922"/></linearGradient></defs>'+''.join(shapes)+'</svg>'
count=0
for path in sorted((ROOT/'game/data/items').glob('*.tres')):
    text=path.read_text()
    if 'res://assets/icons/material.svg' not in text and 'res://assets/icons/trophies/' not in text:continue
    title=re.search(r'display_name = "([^"]+)"',text).group(1)
    key=path.stem.removesuffix('_trophy') if hasattr(str,'removesuffix') else path.stem.replace('_trophy','')
    svg=DEST/(path.stem+'.svg');svg.write_text(art(key,title))
    text=re.sub(r'res://assets/icons/(?:material.svg|trophies/[^\"]+)',f'res://assets/icons/trophies/{svg.name}',text)
    path.write_text(text);count+=1
print('Distinct trophy icons:',count)
