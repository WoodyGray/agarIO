import socket
import pygame
import random

FPS = 200
W_WINDOW, H_WINDOW = 4000, 4000
W_SERV_WINDOW, H_SERV_WINDOW = 300, 300
EAT_SIZE = 15
START_PL_SIZE = 50

mobs_count = 25
eat_count = (W_WINDOW * H_WINDOW) // 80000
colours = {'0': (255, 255, 0), '1': (255, 0, 0), '2': (0, 255, 0), '3': (0, 255, 255), '4': (128, 0, 128)}

def new_R(R, r):
    return (R**2 + r**2)**0.5

def find(s):
    otkr = None
    for i in range(len(s)):
        if s[i] == '<':
            otkr = i
        if s[i] == '>' and otkr is not None:
            zakr = i
            resoult = s[otkr+1:zakr]
            resoult = list(map(int, resoult.split(',')))
            return resoult
    return ''

class Eat():
    def __init__(self, x, y, r, colour):
        self.x = x
        self.y = y
        self.r = r
        self.colour = colour


class Playr():
    def __init__(self, conn, addr, x, y, r, colour):
        self.conn = conn
        self.addr = addr
        self.x = x
        self.y = y
        self.r = r
        self.colour = colour
        self.L = 1

        self.name = 'Mob'
        self.w_window = 1000
        self.h_window = 800
        self.w_vision = 1000
        self.h_vision = 800

        self.errors = 0
        self.ready = False
        self.abs_speed = 30/(self.r**0.5)
        self.speed_x = 0
        self.speed_y = 0

    def set_options(self, data):
        data = data[1:-1].split(' ')
        self.name = data[0]
        self.w_window = int(data[1])
        self.h_window = int(data[2])
        self.w_vision = int(data[1])
        self.h_vision = int(data[2])
        print(self.name, self.w_window, self.h_window)

    def change_speed(self, v):
        if v[0] == 0 and v[1] == 0:
            self.speed_x = 0
            self.speed_y = 0
        else:
            lenv = (v[0]**2 + v[1]**2)**0.5
            v = (v[0] /lenv, v[1] /lenv)
            v = (v[0] * self.abs_speed, v[1]*self.abs_speed)
            self.speed_x, self.speed_y = v[0], v[1]



    def update(self):
        #x координата
        if self.x - self.r <= 0:
            if self.speed_x >= 0:
                self.x += self.speed_x
        else:
            if self.x + self.r > W_WINDOW:
                if self.speed_x <= 0:
                    self.x += self.speed_x
            else:
                self.x += self.speed_x
        # y координата
        if self.y - self.r <= 0:
            if self.speed_y >= 0:
                self.y += self.speed_y
        else:
            if self.y + self.r > W_WINDOW:
                if self.speed_y <= 0:
                    self.y += self.speed_y
            else:
                self.y += self.speed_y

        # абсолютная скорость
        self.abs_speed = 30/(self.r**0.5)

        # радиус
        if self.r >= 100:
            self.r -= self.r/18000

        #масштаб
        if self.r >=self.w_vision/4 or self.r >=self.h_vision/4:
            if self.w_vision <=W_WINDOW or self.h_vision <= H_WINDOW:
                self.L *=2
                self.h_vision = self.h_window * self.L
                self.w_vision = self.w_window * self.L
        if self.r < self.w_vision/8 and self.r < self.h_vision/8:
            if self.L > 1:
                self.L = self.L//2
                self.h_vision = self.h_window * self.L
                self.w_vision = self.w_window * self.L


# настройка и создание сокета
main_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
main_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
main_socket.bind(('localhost', 10000))
main_socket.setblocking(0)
main_socket.listen(5)

#создание граф окна сервера
pygame.init()
screen = pygame.display.set_mode((W_SERV_WINDOW, H_SERV_WINDOW))
clock = pygame.time.Clock()

#создание стартового набора мобов
players = [Playr(None, None, random.randint(0, W_WINDOW),
                 random.randint(0, H_WINDOW),
                 random.randint(10, 100),
                 str(random.randint(0, 4)))
           for _ in range(mobs_count)]

#создание стартового набора еды
eats = [Eat(random.randint(0, W_WINDOW),
            random.randint(0, H_WINDOW),
            EAT_SIZE,
            str(random.randint(0, 4)))
        for _ in range(eat_count)]

tick = -1
run_usl = True
while run_usl:
    tick += 1
    clock.tick(FPS)
    if tick == 200:
        tick = 0
        #проверка на пришедшие заблудшие души
        try:
            new_socket, addr = main_socket.accept()
            print('Подключился', addr)
            new_socket.setblocking(0)
            spawn = random.choice(eats)
            new_playr = Playr(new_socket, addr,
                              spawn.x, spawn.y,
                              START_PL_SIZE, str(random.randint(0, 4)))

            eats.remove(spawn)
            players.append(new_playr)
        except:
            pass
        #дополняем мобов лоускильных
        for i in range(mobs_count -len(players)):
            if len(eats) != 0:
                spawn = random.choice(eats)
                players.append(Playr(None, None, spawn.x, spawn.y, random.randint(10, 100), spawn.colour))
                eats.remove(spawn)

        #дополняем список еды
        new_eats = [Eat(random.randint(0, W_WINDOW),
                        random.randint(0, H_WINDOW),
                        EAT_SIZE,
                        str(random.randint(0, 4)))
                    for i in range(eat_count - len(eats))]
        eats = eats + new_eats

    #считываем команды заблудших душ
    for playr in players:
        if playr.conn is not None:
            try:
                infor = playr.conn.recv(1024)
                infor = infor.decode()
                if infor[0] == '!': #сообщение о готовности к диалогу
                    playr.ready = True
                elif infor[0] == '.' and  infor[-1] == '.': # тех сообщение
                    playr.set_options(infor)
                    playr.conn.send((str(START_PL_SIZE) + ' ' + playr.colour).encode())
                else:# пришел курсор
                    infor = find(infor)
                    playr.change_speed(infor)

            except:
                pass
        else:
            if tick == 100:
                infor = [random.randint(-30, 30), random.randint(-30, 30)]
                playr.change_speed(infor)
        playr.update()

    #определим что видит каждый игрок
    visible_balls = [[] for i in range(len(players))]
    for i in range(len(players)):
        #каких микробов видит i игрок
        for k in range(len(eats)):
            dist_x = eats[k].x - players[i].x
            dist_y = eats[k].y - players[i].y

            # i видит k
            if (
                (abs(dist_x) <= (players[i].w_vision // 2) + eats[k].r)
                and
                (abs(dist_y) <= (players[i].h_vision // 2) + eats[k].r)
                ):
                # i может съесть k
                if (dist_x ** 2 + dist_y ** 2) ** 0.5 <= players[i].r:
                    # изменим радиус i игрока
                    players[i].r = new_R(players[i].r, eats[k].r)
                    eats[k].r = 0
                if players[i].conn is not None and eats[k].r != 0:
                    # подготовим данный к добавлению список видимых душ
                    x_ = str(round(dist_x//players[i].L))
                    y_ = str(round(dist_y//players[i].L))
                    r_ = str(round(eats[k].r//players[i].L))
                    c_ = eats[k].colour

                    visible_balls[i].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_)

        for j in range(i+1, len(players)):
            #переборка всех пар
            dist_x = players[j].x - players[i].x
            dist_y = players[j].y - players[i].y

            # i видит j
            if (
                (abs(dist_x) <=(players[i].w_vision // 2) + players[j].r)
                and
                (abs(dist_y) <=(players[i].h_vision // 2) + players[j].r)
                ):
                #i может съесть j
                if ((dist_x**2 + dist_y**2)**0.5 <= players[i].r and
                        players[i].r > 1.1*players[j].r):
                    #изменим радиус i игрока
                    players[i].r = new_R(players[i].r, players[j].r)
                    players[j].r, players[j].speed_y, players[j].speed_x = 0, 0, 0


                if players[i].conn != None:
                    # подготовим данный к добавлению список видимых душ
                    x_ = str(round(dist_x//players[i].L))
                    y_ = str(round(dist_y//players[i].L))
                    r_ = str(round(players[j].r//players[i].L))
                    c_ = players[j].colour
                    n_ = players[j].name

                    if players[j].r >= 30*players[j].L:
                        visible_balls[i].append(x_+' '+y_+' '+r_+' '+c_+' '+n_)
                    else:
                        visible_balls[i].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_)

            # j видит i
            if (
                (abs(dist_x) <= (players[j].w_vision // 2) + players[i].r)
                and
                (abs(dist_y) <= (players[j].h_vision // 2) + players[i].r)
                ):
                # j может съесть i
                if ((dist_x ** 2 + dist_y ** 2) ** 0.5 <= players[j].r and
                        players[j].r > 1.1 * players[i].r):
                    # изменим радиус j игрока
                    players[j].r = new_R(players[j].r, players[i].r)
                    players[i].r, players[i].speed_y, players[i].speed_x = 0, 0, 0

                if players[j].conn is not None:
                    # подготовим данный к добавлению список видимых душ
                    x_ = str(round(-dist_x//players[j].L))
                    y_ = str(round(-dist_y//players[j].L))
                    r_ = str(round(players[i].r//players[j].L))
                    c_ = players[i].colour
                    n_ = players[i].name

                    if players[i].r >= 30 * players[j].L:
                        visible_balls[j].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_ + ' ' + n_)
                    else:
                        visible_balls[j].append(x_ + ' ' + y_ + ' ' + r_ + ' ' + c_)

    # формируем ответ каждому игроку
    answers = ['' for i in range(len(players))]
    for i in range(len(players)):
        r_ = str(round(players[i].r//players[i].L))
        x_ = str(round(players[i].x//players[i].L))
        y_ = str(round(players[i].y//players[i].L))
        L_ = str(players[i].L)
        visible_balls[i] = [r_+' '+x_+' '+y_+' '+L_] + visible_balls[i]
        answers[i] = '<' + (','.join(visible_balls[i])) + '>'



    # отправляем новое состояние кровавой арены
    for i in range(len(players)):
        if players[i].conn is not None and players[i].ready:
            try:
                players[i].conn.send(answers[i].encode())
                players[i].errors = 0
            except:
                players[i].errors += 1

    # чистим список от откисших игроков
    for playr in players:
        if playr.errors >= 100 or playr.r == 0:
            if playr.conn is not None:
                playr.conn.close()
            players.remove(playr)

    #чистим список от съеденой еды
    for eat in eats:
        if eat.r == 0:
            eats.remove(eat)

    # отрисовка игрового поля на сервере
    for even in pygame.event.get():
        if even.type == pygame.QUIT:
            run_usl = False

    screen.fill('BLACK')
    for playr in players:
        x = round(playr.x * W_SERV_WINDOW / W_WINDOW)
        y = round(playr.y * H_SERV_WINDOW / H_WINDOW)
        r = round(playr.r * W_SERV_WINDOW / W_WINDOW)
        c = colours[playr.colour]
        pygame.draw.circle(screen, c, (x, y), r)
    pygame.display.update()

pygame.quit()
main_socket.close()