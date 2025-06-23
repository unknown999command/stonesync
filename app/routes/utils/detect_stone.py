def detectStone(desc):
    stone = 'Нет ответа ИИ'
    # text = 'Привет, действуй как робот. В этом тексте возможно есть названия камня, они записываются обычно как M-506, S-403 и т.д. Вытащи их и отправь мне только названия, если камней нет - отправь "Нет камня". Текст: ' + str(desc)
    # proxies = {
    #     'http': 'http://CZPfx9De:kwRdhc4S@172.120.163.132:64534',
    #     'https': 'http://CZPfx9De:kwRdhc4S@172.120.163.132:64534',
    # }
    # response = requests.post(
    #     'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=AIzaSyCYwlzcbxa0N5aJSJ6bgfjM0ZKoAzWbmc4',
    #     timeout=5,
    #     headers={'Content-Type': 'application/json'},
    #     data=json.dumps({'contents': [{'parts': [{'text': text}]}]}),
    #     proxies=proxies
    # )
    # stone = response.json()['candidates'][0]['content']['parts'][0]['text'].replace('.', '')
    return stone