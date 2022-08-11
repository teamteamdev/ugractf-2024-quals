import PIL.Image

class DSU:
    def __init__(self, keys):
        self.keys = list(keys)
        self.key_to_idx = {j: i for i, j in enumerate(self.keys)}
        self.data = [-1]*len(self.keys)
    def get(self, key):
        i = self.key_to_idx[key]
        j = i
        while self.data[j] >= 0: j = self.data[j]
        while self.data[i] >= 0: self.data[i], i = j, self.data[i]
        return j
    def join(self, key1, key2):
        i = self.get(key1)
        j = self.get(key2)
        if i == j: return
        if self.data[i] < self.data[j]:
            self.data[j] = i
        else:
            if self.data[i] == self.data[j]: self.data[j] -= 1
            self.data[i] = j

def nonsymmetry_horz(v):
    return len(v[-1] ^ {(v[0] + v[1] - i, j) for i, j in v[-1]})

def nonsymmetry_vert(v):
    return len(v[-1] ^ {(i, v[2] + v[3] - j) for i, j in v[-1]})

def is_symmetric_horz(v):
    return nonsymmetry_horz(v) == 0

def is_symmetric_vert(v):
    return nonsymmetry_vert(v) == 0

def debug_print(x, *args):
    #print(x, *args)
    return x

def print_item(item):
    mtx = bytearray((item[1]-item[0]+2)*(item[3]-item[2]+1)-1)
    mtx[:] = b' '*len(mtx)
    mtx[item[1]-item[0]+1::item[1]-item[0]+2] = b'\n'*(item[3]-item[2])
    for i, j in item[-1]:
        mtx[(j-item[2])*(item[1]-item[0]+2)+(i-item[0])] = b'#'[0]
    debug_print(mtx.decode('ascii'))

def profile(item, which):
    ans = []
    for i in range(item[2*which], item[2*which+1]+1):
        count = 0
        on = False
        for j in range(item[2*(1-which)], item[2*(1-which)+1]+1):
            q = (i, j)[::(1-2*which)] in item[-1]
            if q and not on:
                on = True
                count += 1
            elif not q and on:
                on = False
        if not ans or ans[-1] != count: ans.append(count)
    return ans

def parse_character(item):
    #assert item[1] - item[0] <= 30 and item[3] - item[2] <= 30
    print_item(item)
    debug_print(nonsymmetry_horz(item), nonsymmetry_vert(item))
    if item[1] == item[0] + 2 and item[3] == item[2] + 2 and len(item[-1]) == 9:
        return debug_print('*')
    profile_horz = profile(item, 0)
    profile_vert = profile(item, 1)
    if profile_vert == [1] and nonsymmetry_vert(item) < 25 and nonsymmetry_horz(item) > 50:
        if profile_horz == [1, 2]:
            return debug_print('(')
        elif profile_horz == [2, 1]:
            return debug_print(')')
        else:
            assert False
    if profile_horz == [1, 3, 4, 2, 1] and profile_vert == [1, 2, 1, 2, 1]:
        return debug_print('6')
    elif profile_horz == [1, 2, 3, 2, 1] and profile_vert == [2, 1, 2, 1, 2, 1]:
        return debug_print('5')
    elif profile_horz == [2, 1] and profile_vert == [1]:
        return debug_print('1')
    elif profile_horz == [1] and profile_vert == [1] and is_symmetric_horz(item) and is_symmetric_vert(item):
        return debug_print('+')
    elif profile_horz == [2, 3, 2, 1] and profile_vert == [1, 2, 1, 2, 1] and nonsymmetry_vert(item) < 50:
        return debug_print('3')
    elif profile_horz == [1, 2, 1] and profile_vert == [1, 2, 1] and not is_symmetric_horz(item) and nonsymmetry_vert(item) > 10:
        return debug_print('7')
    elif profile_horz == [1, 2, 1] and profile_vert == [1, 2, 1] and nonsymmetry_vert(item) < 10:
        return debug_print('0')
    elif profile_horz == [2, 3, 4, 2, 1] and profile_vert == [1, 2, 1, 2, 1]:
        return debug_print('8')
    elif profile_horz == [2, 3, 2] and profile_vert == [1, 2, 1, 2, 1] and nonsymmetry_vert(item) > 60:
        return debug_print('2')
    elif profile_horz == [1, 2, 3, 1, 2] and profile_vert == [1, 2, 1]:
        return debug_print('4')
    elif profile_horz == [2, 3, 1] and profile_vert == [1, 2, 1, 2, 1]:
        return debug_print('9')
    assert False, (profile_horz, profile_vert)

def parse_items(items):
    ans = ''
    i = 0
    while i < len(items):
        item = items[i]
        if item[2] == item[3]:
            up = []
            down = []
            i += 1
            while i < len(items) and items[i][0] <= item[1]:
                assert items[i][1] <= item[1]
                if items[i][3] < item[2]:
                    up.append(items[i])
                else:
                    assert items[i][2] > item[3]
                    down.append(items[i])
                i += 1
            if not up and not down:
                assert item[1] == item[0] + 15
                ans += '-'
            else:
                ans += '((%s)/(%s))'%(parse_items(up), parse_items(down))
        else:
            ans += parse_character(item)
            i += 1
    return ans

def parse_image(img):
    w, h = img.size
    data = [[img.getpixel((i, j)) != 255 for i in range(w)] for j in range(h)]
    #print_item((0, w-1, 0, h-1, {(i, j) for i in range(w) for j in range(h) if data[j][i]}))
    dsu = DSU((i, j) for i in range(w) for j in range(h))
    for i in range(h):
        for j in range(w-1):
            if data[i][j] and data[i][j+1]:
                dsu.join((j, i), (j+1, i))
    for i in range(h-1):
        for j in range(w):
            if data[i][j] and data[i+1][j]:
                dsu.join((j, i), (j, i+1))
    sets = {}
    for key in dsu.keys:
        q = dsu.get(key)
        if q not in sets: sets[q] = set()
        sets[q].add(key)
    sets = {k: v for k, v in sets.items() if len(v) > 1}
    items = []
    for k, v in sets.items():
        minx = min(i[0] for i in v)
        maxx = max(i[0] for i in v)
        miny = min(i[1] for i in v)
        maxy = max(i[1] for i in v)
        items.append((minx, maxx, miny, maxy, v))
    items.sort(key=lambda i: (i[0], -i[1]))
    return parse_items(items)

def eval_one(stack):
    left = stack.pop()
    op = stack.pop()
    if op == '+':
        stack[-1] += left
    elif op == '-':
        stack[-1] = left - stack[-1]
    elif op == '*':
        stack[-1] *= left
    elif op == '/':
        stack[-1] = left / stack[-1]
    else:
        assert False, stack

def safe_eval(expr):
    stack = []
    i = len(expr) - 1
    while i >= 0:
        if expr[i].isnumeric():
            j = i
            while j >= 0 and expr[j].isnumeric():
                j -= 1
            stack.append(int(expr[j+1:i+1]))
            i = j
        else:
            c = expr[i]
            i -= 1
            if c in ('+', '-'):
                while len(stack) > 1 and stack[-2] in ('*', '/'):
                    eval_one(stack)
                stack.append(c)
            elif c in ('*', '/', ')'):
                stack.append(c)
            elif c == '(':
                while stack[-2] != ')':
                    eval_one(stack)
                del stack[-2]
            else:
                assert False, c
    while len(stack) > 1:
        eval_one(stack)
    return +stack[0]

if __name__ == '__main__':
    import sys
    expr = parse_image(PIL.Image.open(sys.argv[1]).convert('L'))
    print(expr)
    print(safe_eval(expr))
