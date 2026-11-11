"""Лабораторная работа № 5. Вариант 19. Ситникова Ольга, группа БИ2-1."""
import math  # корень из 5 для константы метода умножения
import platform  # сведения о компьютере
import random  # случайные ключи
import time  # замер времени
from collections import Counter  # подсчёт распределения длин цепочек
import matplotlib.pyplot as plt  # графики

N, M = 60_000, 99_991  # число ключей и размер таблицы по варианту 19 (M простое)
A = (math.sqrt(5) - 1) / 2  # константа метода умножения, около 0,618


def h_mul(k, m):  # хеш-функция метода умножения
    return int(m * ((k * A) % 1))  # дробная часть k*A, умноженная на m, с отбрасыванием дробной части


def h_bad(k, m):  # заведомо неудачная хеш-функция (для сравнения)
    return k % 10  # возможны только 10 различных значений


def h2(k, m):  # вторая хеш-функция (шаг при двойном хешировании)
    return 1 + k % (m - 1)  # шаг от 1 до m-1; так как m простое, шаг взаимно прост с m


class ChainTable:  # хеш-таблица с методом цепочек
    def __init__(self, m, h=h_mul):  # размер таблицы и хеш-функция
        self.m, self.h, self.n, self.probes = m, h, 0, 0  # параметры, число элементов, счётчик проб
        self.slots = [[] for _ in range(m)]  # каждая ячейка хранит свой список пар (ключ, значение)

    def insert(self, key, value):  # вставка (или обновление) пары
        chain = self.slots[self.h(key, self.m)]  # цепочка нужной ячейки
        for i, (k, _) in enumerate(chain):  # ищем ключ в цепочке
            self.probes += 1  # считаем просмотренный элемент
            if k == key:  # ключ уже есть
                chain[i] = (key, value)  # обновляем значение
                return  # вставка закончена
        chain.append((key, value))  # ключа нет: добавляем в конец цепочки
        self.n += 1  # увеличиваем число элементов

    def search(self, key):  # поиск значения по ключу
        for k, v in self.slots[self.h(key, self.m)]:  # просматриваем цепочку ячейки
            self.probes += 1  # считаем просмотренный элемент
            if k == key:  # нашли ключ
                return v  # возвращаем значение
        return None  # в цепочке ключа нет

    def delete(self, key):  # удаление по ключу
        chain = self.slots[self.h(key, self.m)]  # цепочка нужной ячейки
        for i, (k, _) in enumerate(chain):  # ищем ключ
            self.probes += 1  # считаем просмотренный элемент
            if k == key:  # нашли
                del chain[i]  # убираем пару из цепочки
                self.n -= 1  # уменьшаем число элементов
                return True  # удаление выполнено
        return False  # ключа не было


class DoubleHashTable:  # хеш-таблица с открытой адресацией и двойным хешированием
    EMPTY, DELETED = object(), object()  # метки «пусто» и «удалено» (tombstone)

    def __init__(self, m, h=h_mul):  # размер таблицы и первая хеш-функция
        self.m, self.h, self.n, self.probes = m, h, 0, 0  # параметры, число элементов, счётчик проб
        self.keys = [self.EMPTY] * m  # массив ключей, сначала все ячейки пусты
        self.vals = [None] * m  # массив значений

    def _seq(self, key):  # последовательность проб h_i(k) = (h1 + i*h2) mod m
        pos, step = self.h(key, self.m), h2(key, self.m)  # начальная позиция и шаг
        for _ in range(self.m):  # не больше m проб
            yield pos  # отдаём очередную позицию
            pos = (pos + step) % self.m  # переходим к следующей позиции

    def insert(self, key, value):  # вставка (или обновление) пары
        free = None  # первая подходящая для записи ячейка
        for pos in self._seq(key):  # идём по последовательности проб
            self.probes += 1  # считаем пробу
            k = self.keys[pos]  # ключ в текущей ячейке
            if k == key:  # ключ уже есть
                self.vals[pos] = value  # обновляем значение
                return  # вставка закончена
            if k is self.DELETED and free is None:  # запоминаем первую «удалённую» ячейку
                free = pos  # сюда можно записать, если ключа дальше нет
            if k is self.EMPTY:  # дошли до пустой ячейки: ключа в таблице нет
                free = pos if free is None else free  # выбираем место для записи
                break  # дальше искать не нужно
        if free is None:  # свободных ячеек не нашлось
            raise RuntimeError("Таблица переполнена")  # сообщаем об ошибке
        self.keys[free], self.vals[free] = key, value  # записываем пару
        self.n += 1  # увеличиваем число элементов

    def search(self, key):  # поиск значения по ключу
        for pos in self._seq(key):  # идём по последовательности проб
            self.probes += 1  # считаем пробу
            k = self.keys[pos]  # ключ в текущей ячейке
            if k is self.EMPTY:  # пустая ячейка обрывает поиск
                return None  # ключа нет
            if k == key:  # нашли ключ
                return self.vals[pos]  # возвращаем значение
        return None  # просмотрена вся таблица, ключа нет

    def delete(self, key):  # удаление по ключу
        for pos in self._seq(key):  # идём по последовательности проб
            self.probes += 1  # считаем пробу
            k = self.keys[pos]  # ключ в текущей ячейке
            if k is self.EMPTY:  # пустая ячейка: ключа нет
                return False  # удалять нечего
            if k == key:  # нашли ключ
                self.keys[pos], self.vals[pos] = self.DELETED, None  # ставим метку «удалено», а не обнуляем
                self.n -= 1  # уменьшаем число элементов
                return True  # удаление выполнено
        return False  # ключа не было


class StdDict(dict):  # обёртка над встроенным dict с тем же интерфейсом (задание В5)
    probes = 0  # у dict пробы не считаются

    def insert(self, key, value):  # вставка
        self[key] = value  # обычная запись в словарь

    def search(self, key):  # поиск
        return self.get(key)  # значение или None


def check(table, keys):  # проверка методов insert, search и delete
    for k in keys:  # вставляем все ключи
        table.insert(k, k)  # значением служит сам ключ
    for k in keys[::2]:  # удаляем каждый второй ключ
        assert table.delete(k)  # удаление должно пройти успешно
    assert all(table.search(k) is None for k in keys[::2])  # удалённые ключи не находятся
    assert all(table.search(k) == k for k in keys[1::2])  # остальные ключи по-прежнему находятся


def measure(table, keys, hits, misses):  # замер вставки и двух видов поиска
    t0 = time.perf_counter()  # начало замера вставки
    for k in keys:  # вставляем все ключи
        table.insert(k, k)  # одна вставка
    res = [time.perf_counter() - t0]  # общее время вставки, с
    for qs in (hits, misses):  # сначала успешные, затем неуспешные запросы
        table.probes = 0  # обнуляем счётчик проб
        t0 = time.perf_counter()  # начало замера поиска
        for q in qs:  # выполняем запросы
            table.search(q)  # один поиск
        res += [(time.perf_counter() - t0) / len(qs), table.probes / len(qs)]  # время и пробы на запрос
    return res  # [вставка, время успеха, пробы успеха, время неуспеха, пробы неуспеха]


if __name__ == "__main__":  # запуск только при прямом старте файла
    print(platform.platform(), "|", platform.processor() or platform.machine(), "| Python", platform.python_version())  # система
    rng = random.Random(42)  # генератор с фиксированным seed
    pool = rng.sample(range(10_000_000), 105_000)  # уникальные случайные целые ключи
    keys_of = lambda n: pool[:n]  # первые n ключей из набора
    misses = pool[-10_000:]  # 10 000 заведомо отсутствующих ключей (конец набора)
    hits_of = lambda n: rng.choices(pool[:n], k=10_000)  # 10 000 успешных запросов
    check(ChainTable(1009), pool[:500])  # проверка цепочек на малой таблице
    check(DoubleHashTable(1009), pool[:500])  # проверка двойного хеширования на малой таблице
    print(f"Проверка insert/search/delete пройдена. n = {N}, m = {M}, alpha = {N / M:.3f}\n")  # сообщение
    hits, chain = hits_of(N), ChainTable(M)  # запросы и таблица цепочек для основного опыта
    for name, t in (("Цепочки", chain), ("Двойное хеширование", DoubleHashTable(M)), ("dict", StdDict())):  # три реализации
        r = measure(t, keys_of(N), hits, misses)  # замеры на одних и тех же данных
        print(f"{name:<20} вставка {r[0]:.4f} с | поиск {r[1] * 1e6:.3f} мкс, проб {r[2]:.2f} | промах {r[3] * 1e6:.3f} мкс, проб {r[4]:.2f}")  # строка результата
    lens = Counter(len(c) for c in chain.slots)  # сколько ячеек имеют цепочку каждой длины
    print("Распределение длин цепочек:", dict(sorted(lens.items())))  # печатаем распределение
    print("\nСравнение хеш-функций (цепочки, n = 60000):")  # заголовок сравнения
    for name, h in (("Умножения", h_mul), ("k mod 10", h_bad)):  # хорошая и плохая функции
        t = ChainTable(M, h)  # новая таблица с выбранной функцией
        r = measure(t, keys_of(N), hits, misses)  # замеры
        used = sum(1 for c in t.slots if c)  # число занятых ячеек
        print(f"{name:<10} занято ячеек {used}, коллизий {N - used}, макс. цепочка {max(map(len, t.slots))}, проб при поиске {r[2]:.1f}, вставка {r[0]:.2f} с")  # результат
    alphas = [0.1, 0.3, 0.5, 0.7, 0.9, 0.95]  # значения коэффициента заполнения
    exp = {"Двойное, успешный": [], "Двойное, неуспешный": [], "Цепочки, успешный": []}  # результаты для графика
    print("\nalpha | двойное: успех / промах | цепочки: успех / промах | время успешного поиска, мкс (двойное / цепочки)")  # заголовок
    for a in alphas:  # перебираем alpha
        n = int(a * M)  # число ключей для данного alpha
        hs = hits_of(n)  # успешные запросы для n ключей
        d = measure(DoubleHashTable(M), keys_of(n), hs, misses)  # двойное хеширование
        c = measure(ChainTable(M), keys_of(n), hs, misses)  # цепочки
        exp["Двойное, успешный"].append(d[2])  # пробы при успешном поиске
        exp["Двойное, неуспешный"].append(d[4])  # пробы при неуспешном поиске
        exp["Цепочки, успешный"].append(c[2])  # пробы цепочек при успешном поиске
        print(f"{a:.2f}  | {d[2]:.2f} / {d[4]:.2f} | {c[2]:.2f} / {c[4]:.2f} | {d[1] * 1e6:.3f} / {c[1] * 1e6:.3f}")  # строка таблицы
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))  # два графика рядом
    for name, ys in exp.items():  # экспериментальные линии
        ax1.plot(alphas, ys, "o-", label=name)  # проб в зависимости от alpha
    xs = [i / 100 for i in range(5, 97)]  # плотная сетка alpha для теоретической кривой
    ax1.plot(xs, [1 / (1 - x) for x in xs], "k--", label="Теория 1/(1-α)")  # теория для неуспешного поиска
    ax1.set(xlabel="α", ylabel="Среднее число проб", title="Пробы в зависимости от α", yscale="log")  # оформление
    ax2.bar(list(lens), list(lens.values()))  # столбики: длина цепочки -> число ячеек
    ax2.set(xlabel="Длина цепочки", ylabel="Число ячеек", title="Распределение длин цепочек (α = 0,6)")  # оформление
    ax1.legend()  # легенда левого графика
    ax1.grid(True, alpha=0.3)  # сетка левого графика
    plt.tight_layout()  # убираем наложение подписей
    plt.savefig("lab5_graphs.png", dpi=150)  # сохраняем график для отчёта
    plt.show()  # показываем график на экране
