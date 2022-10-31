import socket
import pygame
import random


W_WINDOW, H_WINDOW = 600, 600
colours = {'0': (255, 255, 0), '1': (255, 0, 0), '2': (0, 255, 0), '3': (0, 255, 255), '4': (128, 0, 128)}
my_name = 'ЗАСОС'
grid_colour = (150, 150, 150)

def draw_opponents(enemy_list):
    for i in range(len(enemy_list)):
        j = enemy_list[i].split()

        x = W_WINDOW//2 + int(j[0])
        y = H_WINDOW // 2 + int(j[1])
        r = int(j[2])
        c = colours[j[3]]
        pygame.draw.circle(screen, c, (x, y), r)

        if len(j) == 5 : write_name(x, y, r, j[4])

def find(s):
    otkr = None
    for i in range(len(s)):
        if s[i] == '<':
            otkr = i
        if s[i] == '>' and otkr is not None:
            zakr = i
            res = s[otkr+1:zakr]
            return res
    return ''

def write_name(x, y, r, name):
    font = pygame.font.Font(None, r)
    text = font.render(name, True, (0, 0, 0))
    rect = text.get_rect(center=(x, y))
    screen.blit(text, rect)


class Me():
    def __init__(self, data):
        data = data.split()
        self.r = int(data[0])
        self.colour = data[1]

    def update(self, new_r):
        self.r = new_r

    def draw(self):
        if self.r != 0:
            pygame.draw.circle(screen, colours[self.colour],
                               (W_WINDOW // 2, H_WINDOW // 2), self.r)
            write_name(W_WINDOW // 2, H_WINDOW // 2, self.r, my_name)

class Grid():
    def __init__(self, screen):
        self.screen = screen
        self.x = 0
        self.y = 0
        self.start_size = 200
        self.size = self.start_size

    def update(self, r_x, r_y, L):
        self.size = self.start_size//L
        self.x = -self.size + (-r_x) % self.size
        self.y = -self.size + (-r_y) % self.size

    def draw(self):
        for i in range(W_WINDOW//self.size + 2):
            pygame.draw.line(self.screen, grid_colour,
                             [self.x + i*self.size, 0],#координаты верхнего конца
                             [self.x + i*self.size, H_WINDOW],#координаты нижнего конца
                             1)
        for i in range(H_WINDOW//self.size + 2):
            pygame.draw.line(self.screen, grid_colour,
                             [0, self.y + i*self.size],#координаты верхнего конца
                             [W_WINDOW, self.y + i*self.size],#координаты нижнего конца
                             1)



#создание поля игры
pygame.init()
screen = pygame.display.set_mode((W_WINDOW, H_WINDOW))
pygame.display.set_caption('заблудшие гавнарики')

#подрубаем сервак
klient_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
klient_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
klient_socket.connect(('172.18.4.10', 10000))

# отправляем свой ник и размеры окна
klient_socket.send(('.' + my_name + ' ' + str(W_WINDOW) + ' ' + str(H_WINDOW) + '.').encode())

#получаемсвой размер и цвет
data = klient_socket.recv(64).decode()

#подтверждаем получение
klient_socket.send('!'.encode())

me = Me(data)
grid = Grid(screen)

old_vector = (0, 0)
vector = (0, 0)
run_usl = True
while run_usl:
    #обработка событий
    for even in pygame.event.get():
        if even.type == pygame.QUIT:
            run_usl = False
    #считаем положение мыши
    if pygame.mouse.get_focused():
        pos = pygame.mouse.get_pos()
        vector = (pos[0] - (W_WINDOW // 2), pos[1] - (H_WINDOW // 2))

        if vector[0]**2 + vector[1]**2 <= me.r**2:
            vector = (0, 0)

    #отправляем вектор направления если он поменялся
    if vector != old_vector:
        old_vector = vector
        message = '<' + str(vector[0]) + ',' + str(vector[1]) + '>'
        klient_socket.send(message.encode())

    #получаем новое состояние поля
    try:
        infor = klient_socket.recv(2**13)
    except:
        run_usl = False
        continue
    infor = infor.decode()
    infor = find(infor)
    infor = infor.split(',')

    #обработка сообщения сервера
    if infor != ['']:
        parametrs = list(map(int, infor[0].split(' ')))
        me.update(parametrs[0])
        grid.update(parametrs[1], parametrs[2], parametrs[3])
        # рисуем новое сотояние поля
        screen.fill('gray25')
        grid.draw()
        draw_opponents(infor[1:])
        me.draw()


    pygame.display.update()
pygame.quit()