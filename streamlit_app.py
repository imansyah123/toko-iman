import pygame
import random
import sys

pygame.init()

# --- SETTING LAYAR ---
LEBAR, TINGGI = 800, 600
layar = pygame.display.set_mode((LEBAR, TINGGI))
pygame.display.set_caption("PERANG 3D - TOKO IMAN vs MALING")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)

# --- WARNA ---
HIJAU = (34, 139, 34)
MERAH = (220, 20, 60)
KUNING = (255, 215, 0)
PUTIH = (255, 255, 255)
HITAM = (0, 0, 0)

# --- PLAYER (BOS IMAN) ---
player_x = LEBAR // 2
player_y = TINGGI - 80
player_hp = 100
player_speed = 6
peluru_list = []
kill = 0

# --- MUSUH ---
musuh_list = []
for i in range(5):
    musuh_list.append([random.randint(0, LEBAR-40), random.randint(-600, -40), random.randint(2, 4)])  # x, y, speed

def gambar_player(x, y):
    pygame.draw.rect(layar, (0, 100, 255), (x, y, 50, 30)) # badan
    pygame.draw.circle(layar, (255, 220, 180), (x+25, y-10, 15)) # kepala
    pygame.draw.rect(layar, HITAM, (x+20, y-35, 10, 20)) # senjata

def gambar_musuh(x, y):
    pygame.draw.rect(layar, MERAH, (x, y, 40, 40))
    pygame.draw.circle(layar, HITAM, (x+10, y+10, 
