import asyncio
import edge_tts

async def test_edge_tts():
    voices = await edge_tts.list_voices()
    kk_voices = [v for v in voices if 'kk' in v['Locale'].lower()]
    ru_voices = [v for v in voices if 'ru' in v['Locale'].lower()]
    print("Kazakh voices:", [v['ShortName'] for v in kk_voices])
    print("Russian voices:", [v['ShortName'] for v in ru_voices])
    
    text = "Сәлем, бұл сынақ дауысы. Здравствуйте, это проверка голоса."
    voice = "kk-KZ-AigulNeural" if kk_voices else (ru_voices[0]['ShortName'] if ru_voices else 'en-US-AriaNeural')
    
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("test_edge.mp3")
    print(f"Saved audio using {voice}")

if __name__ == "__main__":
    asyncio.run(test_edge_tts())
