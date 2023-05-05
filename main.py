from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import re
from typing import Dict
import copy
import json

app = FastAPI()

html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">

</head>
<body>

<div id="cont" class="container">
<!--    <button py-click="bez.test()"></button>-->
<!--    <button py-click="bez.main()">Main</button>-->

    <div id="test">Hello</div>
    
    <form action="" onsubmit="sendMessage(event)">
        <label for="messageText" class="form-label">Encoded text:</label>
        </br>
        <textarea class="form-control" type="text" id="messageText" autocomplete="off"></textarea>
        </br>
        <button class="btn btn-success col-lg-3">Send</button>
    </form>
    <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                if (!isNaN(event.data.slice(0, 2))){
                    var progress = document.getElementById('progress')
                    progress.style = "width: " + event.data.slice(0, 2) + "%";
                    console.log(event.data);
                    document.getElementById('key').innerHTML = event.data.slice(2, -1)
                } else {
                    document.getElementById('progress').style = "width: 100%";
                    const text = document.createElement("div");
                    text.innerHTML = event.data;
                    document.getElementById('cont').appendChild(text);
                }
            };
            function sendMessage(event) {
                console.log("ssss");
                var input = document.getElementById("messageText")
                ws.send(input.value)
                event.preventDefault()
            }
    </script>
    <br>
    <br>

    <div class="progress">
      <div id="progress" class="progress-bar bg-success" role="progressbar" style="width: 0" aria-valuenow="25" aria-valuemin="0" aria-valuemax="100"></div>
    </div>

    <br>
    <br>
    
    <div class="row" id="key">
    </div>
    
    </br>
    
</div>
    </body>
</html>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>

</body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # while True:

    data = await websocket.receive_text()
    encoded_text = data
    sample_text = open('stats.txt', 'r', encoding='UTF-8').read().replace('www.bizdin.kg', '')

    counted_chars = count_chars(sample_text)
    counted_encoding_chars = count_chars(encoded_text)

    _, encoded_words = count_words(encoded_text)
    _, sample_words = count_words(sample_text)

    key = dict()
    for ec in counted_encoding_chars:
        key[ec[0]] = None

    key[counted_encoding_chars[0][0]] = 'а'
    # key[counted_encoding_chars[2][0]] = 'н'
    # key[counted_encoding_chars[1][0]] = 'к'

    counted_encoding_chars_dict = dict(counted_encoding_chars)
    counted_chars_dict = dict(counted_chars)

    print(counted_chars)
    print(counted_encoding_chars)

    unknown_chars = ''.join([c[0] for c in counted_chars[2:]])

    print(unknown_chars)

    print(key)

    # bias = 0.05

    must_words = ["баатыр", 'манас', 'каныкей']

    for word in must_words:
        matches = match_words(encoded_words, generate_pattern(word, key, counted_encoding_chars))
        print(matches)
        if len(matches) == 1:
            for i in range(len(word)):
                key[matches[0][i]] = word[i]

    while all(map(lambda x: x is not None, key.keys())):
        print(key)
        pr = 0

        tts = ""

        for k in key:
            tts += f'<h6 class="col-lg-6">{k} : {key.get(k, "X")}</h6> '
            if key[k] is not None:
                pr += 1

        await websocket.send_text(str(int(pr*100/36)) + tts)

        examples = []

        for word in encoded_words:
            if is_checkable(word, key):
                reg = ''

                for s in word:
                    if key.get(s, None) is None:
                        reg += f'[{get_unknown_chars(key)}]'
                    else:
                        reg += key[s]

                reg += '$'

                # print(word, reg)

                matches = match_words(sample_words, reg)

                if word == 'лңк':
                    print(matches, reg)
                matches = list(filter(lambda x: check_pattern(x, word), matches))

                # if matches:
                #     print(matches)

                if len(matches) == 1 and any(map(lambda s: s not in key.values(), matches[0])):
                    # print(matches[0])
                    err = 0.0
                    is_valid = True

                    for i in range(len(matches[0])):
                        if key[word[i]] is None:
                            err += abs(
                                counted_encoding_chars_dict[word[i]] * 1.0 / counted_chars_dict[matches[0][i]] - 1)

                            if matches[0][i] in list(key.values()):
                                is_valid = False
                                break

                    if is_valid:
                        examples.append((word, matches[0], err / len(word)))

        if len(examples) == 0:
            break

        examples.sort(key=lambda x: x[2])

        for i in range(len(examples[0][0])):
            key[examples[0][0][i]] = examples[0][1][i]

        print(examples[0])

    text = ''

    for w in encoded_text:
        if w.isalpha():
            upp = w != w.lower()
            w = w.lower()
            text += (key[w] if not upp else key[w].upper()) if key.get(w, None) is not None else 'X'
        elif w == '\n':
            text += w + '</br>'
        else:
            text += w

    print(''.join([k for k in key.values() if k is not None]))
    print(''.join([k for k in key.keys() if key[k] is not None]))
    print(text)
    print(key)

    await websocket.send_text(text)

    # print(sample_words)

    print(list(key.values()).count(None))

    print(match_words(sample_words, 'мо.$'))
    print(match_words(encoded_words, 'лңк'))
    print(get_unknown_chars(key))

def validate(word):
    return ''.join(i for i in word if i.isalpha())


def match_words(words, reg):
    return list(filter(lambda w: re.match(reg, w), words))


def count_words(text: str):
    words = map(validate, text.lower().split())
    word_dict = dict()
    tot = 0
    for word in words:
        words_same_size = word_dict.get(len(word), dict())
        words_same_size[word] = words_same_size.get(word, 0) + 1
        tot += 1

        word_dict[len(word)] = words_same_size

    for k in word_dict:
        for j in word_dict[k]:
            word_dict[k][j] /= tot * 0.01

    for k in word_dict:
        si = list(word_dict[k].items())
        si.sort(key=lambda x: -x[1])
        word_dict[k] = si

    # for i in si:
    #     print(f'"{i[0]}" : {i[1]}')

    return word_dict, set(map(validate, text.lower().split()))


def count_chars(s):
    s = s.lower()
    d = dict()
    tot = 0
    for c in s:
        if c.isalpha() and c not in "quote":
            d[c] = d.get(c, 0) + 1
            tot += 1

    for k in d:
        d[k] /= tot * 0.01

    si = list(d.items())
    si.sort(key=lambda x: -x[1])

    return si


def is_checkable(word, key):
    for k in key:
        if key[k] is not None and k in word:
            return True
    return False


def get_unknown_chars(key: Dict):
    alph = 'абвгдеёжзийклмнопрстуфчцчшщъыьэюяңөү'
    return ''.join((c for c in alph if c not in key.values()))


def get_unknown_keys(key):
    return ''.join((c for c in list(key.keys()) if key[c] is None))


def check_pattern(match, word):
    for i in range(len(word) - 1):
        for j in range(i, len(word)):
            if not ((match[i] == match[j]) == (word[i] == word[j])):
                return False
    return True


def generate_pattern(word, key, counted_encoding_chars):
    reg = ''
    for s in word:
        if s in key.values():
            reg += list(key.keys())[list(key.values()).index(s)]
        elif s in 'нкы':
            reg += f'[{"".join(c[0] for c in counted_encoding_chars[1:4])}]'
        else:
            reg += f'[{get_unknown_keys(key)}]'

    print(reg)
    return reg + '$'
