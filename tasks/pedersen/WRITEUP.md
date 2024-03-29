# Pedersen: Write-up

Мы попадаем в магазин, где у нас есть две опции:

- получить кошелёк с балансом 100 ₽
- купить флаг, предоставив кошелёк с балансом 1 337 ₽ или больше

Получим произвольный кошелёк, чтобы с ним работать:

```
eyJjb21taXRtZW50IjoiNWEwNTc1ZTZkODlhMmIyMWRiNWQ1MGE1OWU3MjNiNWE0MThlNTkyNmUzZDg1OGJjOTA1YTg5MDM4ZGM5Yjk3ZCIsImJsaW5kaW5nIjoiMjIzZDFjNzNiMmE5YTlmZGIzYzU3M2YzYWY0M2ZjNjQ2Njc2Mjk1Mzg2YjA2YjU4NDdkYTE4YWI5N2MyNWEwYSIsImJhbGFuY2UiOjEwMH0=
```

Декодируем base64 и обнаружим внутри JSON:

```json
{
  "commitment": "5a0575e6d89a2b21db5d50a59e723b5a418e5926e3d858bc905a89038dc9b97d",
  "blinding": "223d1c73b2a9a9fdb3c573f3af43fc646676295386b06b5847da18ab97c25a0a",
  "balance": 100
}
```

В исходном коде нас будет интересовать всего один файл — [`crypto.rs`](app/src/crypto/crypto.rs), который и отвечает за формирование и проверку кошельков. Находим [библиотеку `bulletproofs`](app/Cargo.toml#L9), в которой реализовано нечто под названием [`PedersenGens`](https://doc-internal.dalek.rs/bulletproofs/struct.PedersenGens.html). Из документации узнаём, что мы имеем дело с вещью под названием «схема обзяательства Педерсена».

> _Схема обязательств_ — это криптографический примитив, который позволяет зафиксировать ту или иную информацию, не раскрывая её.
>
> Представьте, что вы написали что-то на листе бумаги, запечатали его в конверт и отдали кому-то ещё. Этот человек не может увидеть содержимое конверта, а вы не можете его изменить. Схема обязательств — это математический способ сделать как бы то же самое: на *фазе передачи* вы сообщаете некую вспомогательную информацию о сообщении, не раскрывающую ваше сообщение; а на *фазе раскрытия* вы сообщаете само сообщение. При этом вспомогательная информация должна быть сформирована так, чтобы по сообщению можно было проверить, что оно действительно ей соответствует, а значит, не изменялось.

Схема Педерсена работает следующим образом:

1. Выбирается некая группа с порядком $p$ и два генератора в ней — $g$ и $h$. Они публичные и известны.
2. Берётся сообщение $m$.
3. Генерируется случайное целое число $r$ (blinding factor) и вычисляется $C = g^m \times h^r$. Числа $C$ (commitment) и  $r$ сообщаются на фазе передачи.
4. На фазе раскрытия сообщается само сообщение $m$.

После четвёртого шага второй стороне легко проверить, что сообщение действительно не подменено. При этом самостоятельно вычислить $m$ трудно — для этого придётся решить задачу [дискретного логарифмирования](https://ru.wikipedia.org/wiki/%D0%94%D0%B8%D1%81%D0%BA%D1%80%D0%B5%D1%82%D0%BD%D0%BE%D0%B5_%D0%BB%D0%BE%D0%B3%D0%B0%D1%80%D0%B8%D1%84%D0%BC%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5).

В нашем задании используется [группа точек](https://ru.wikipedia.org/wiki/%D0%AD%D0%BB%D0%BB%D0%B8%D0%BF%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B0%D1%8F_%D0%BA%D1%80%D0%B8%D0%B2%D0%B0%D1%8F#%D0%93%D1%80%D1%83%D0%BF%D0%BF%D0%BE%D0%B2%D0%BE%D0%B9_%D0%B7%D0%B0%D0%BA%D0%BE%D0%BD) на эллиптической кривой [Ristretto255](https://ristretto.group/). Всё, что нам нужно знать на этом этапе, что в такой группе «возведением в степень» является умножение точки на число, а «умножением» — сумма точек.

Давайте теперь посмотрим, что происходит на самом деле в задании:

1. Заранее задан некий секрет $x$ — 256-битное число.
2. В качестве кошелька предоставлется обязательство для $x + balance$.

Давайте посмотрим, например, на обязательства для баланса 100 и баланса 101:

* баланс 100: $C_{100} = g^{x+100} \times h^r$
* баланс 101: $C_{101} = g^{x+101} \times h^r = g^{x+100} \times h^r \times g$

Обратим внимание, что $g$ и $h$ известны — в конкретно нашем случае это [стандартные генераторы](https://doc-internal.dalek.rs/src/bulletproofs/generators.rs.html#36) библиотеки `bulletproofs`.

Получается, можно просто умножить коммитмент на генератор, оставив то же случайное значение, и получить корректный кошелёк с увеличенным на единицу балансом.

Осталось лишь заметить, что никто не мешает нам повторить этот трюк ещё 1236 раз — и получить баланс не 101, а нужные нам 1337.

Чтобы не разбираться самому с тем, как всё закодировано, прямо в полученном проекте заменим `backend.rs` на наш эксплоит, скопировав нужные функции по кодированию и декодированию точек из хексов из уже написанного кода.

[Эксплоит](exploit.rs)

Флаг: **ugra_math_is_always_an_evil_creature_nprlwcfpbgwg**
