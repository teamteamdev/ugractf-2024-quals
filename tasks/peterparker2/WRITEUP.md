# Сложная: Write-up

Это задание — усложненная версия [Несложной](../peterparker), в которой добавлены меры против решения "отправим много раз 0 пока не получим флаг". Изменения таковы:

- За каждые 5 неправильных ответов подряд требуется пройти на 10 больше капч.
- Все выражения далеки от целых чисел, чтобы нельзя было угадать ответ "0", "1" и тому подобное.

С такими изменениями единственным адекватным методом решения становится автоматическое решение примеров.

Можно воспользоваться публичным API, например предоставляемым [Photomath](https://rapidapi.com/apidojo/api/photomath1).

Можно воспользоваться и локальным решением, использующим для распознавания примеров нейросеть, например [pix2tex](https://pypi.org/project/pix2tex/), а для вычисления значения выражения — хотя бы даже `eval`. Это решение можно видеть в файле [solve.py](solve.py).

Можно, наконец, [распарсить формулу без нейронки](writeup/equation.py), опираясь на то, что в генераторе капчи используется фиксированный шрифт. Подобный подход более трудозатратен, но для некоторых участников может оказаться более простым.

Флаг: **ugra_peterparker2_final_release_LASTVERSION_u66fei8xzbde**
