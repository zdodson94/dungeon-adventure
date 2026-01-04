#!/usr/bin/env python3

from random import choices, randint
from string import ascii_uppercase
from collections import defaultdict
from print import slow_print
from monsters import available_monsters
from items import Elixir, SuperElixir, MegaElixir
from weapons import VegaBlade, CygnusHammer
from spells import Eclipse, Supernova


chest_sizes = {
  'small'  : 0.5,
  'medium' : 0.3,
  'large'  : 0.15,
  'huge'   : 0.05
}
chest_size_to_iron = {
  'small'  : 100,
  'medium' : 500,
  'large'  : 1000,
  'huge'   : 5000
}
chest_items = [None, Elixir(), SuperElixir(), MegaElixir()]
chest_size_to_item_weights = {
  'small'  : [0.60, 0.33, 0.05, 0.02],
  'medium' : [0.50, 0.30, 0.15, 0.05],
  'large'  : [0.35, 0.20, 0.35, 0.10],
  'huge'   : [0.20, 0.10, 0.20, 0.50]
}
max_chests_per_room = 3
max_number_monsters_per_room = 2

class TreasureChest:
  def __init__(self):
    self.size = choices(list(chest_sizes.keys()), weights=list(chest_sizes.values()))[0]
    self.iron = chest_size_to_iron[self.size]
    self.item = choices(chest_items, weights=chest_size_to_item_weights[self.size])[0]

class Room:
  def __init__(self, doors, dist_frac):
    self.doors = doors
    self.monsters = []
    self.treasure = []
    self.generate(dist_frac)

class NormalRoom(Room):
  def generate(self, dist_frac):
    for _ in range(randint(1, max_chests_per_room)):
      self.treasure.append(TreasureChest())
    for _ in range(randint(1, max_number_monsters_per_room)):
      modified_weights = [v * dist_frac if idx > 1 else v for idx, v in enumerate(available_monsters.values())]
      modified_weights = [v / sum(modified_weights) for v in modified_weights]
      self.monsters.append(choices(list(available_monsters.keys()), weights=modified_weights)[0]())
      monster_dict = defaultdict(int)
      for monster in self.monsters:
        monster_dict[monster.name] += 1
      for k, v in monster_dict.items():
        if v > 1:
          for monster, letter in zip(self.monsters, ascii_uppercase):
            if monster.name == k:
              monster.name += f' {letter}'
  def describe(self, player):
    slow_print(f'You are in a room with:')
    slow_print(f' - {len(self.doors)} doors')
    for door in self.doors:
      slow_print(f'   - a door to the ({door[0]}){door[1:]}')
    if self.treasure:
      slow_print(f' - {len(self.treasure)} chest(s)')
      for chest in self.treasure:
        slow_print(f'   - a {chest.size} chest')
    if self.monsters:
      slow_print(f' - {len(self.monsters):n} enemies')
    for monster in self.monsters:
      slow_print(f'   - {monster.name}')

class MerchantRoom(Room):
  def generate(self, dist_frac):
    self.items = [
      Elixir(),
      SuperElixir(),
      MegaElixir(),
      VegaBlade(),
      CygnusHammer(),
      Eclipse(),
      Supernova()
    ]
    self.not_defeated = True
    self.antagonized = False
  def describe(self, player):
    if self.not_defeated and not self.antagonized:
      slow_print('A warped halo of light gazes through you from the void.')
      slow_print('"Iron for wares..."')
      slow_print('The voice rends the silence and shakes your core...')
    elif self.antagonized:
      slow_print('Suddenly you are small, and you gaze up at something your mind cannot fathom...')
    else:
      slow_print('This room contains nothing.')

class NebulaRoom(Room):
  def generate(self, dist_frac):
    self.AP = randint(3, 8)
    self.done = False
  def describe(self, player):
    slow_print('You are in a silent nursery of power...')
    slow_print('A low hum accompanies the tiny points of light that surround you.')
    if not self.done:
      slow_print('You feel that light inhabit your corporeal form...')
      slow_print(f'You heal fully and gain {self.AP} AP!')
      player.hp = player.max_hp
      player.attribute_points += self.AP
      self.done = True

class Map:
  def __init__(self, size, fill_value=None):
    self.size = size
    self.map = [[fill_value for _ in range(self.size)] for _ in range(self.size)]

  def get_location(self, location):
    return self.map[location[0]][location[1]]

  def set_location(self, location, value):
    self.map[location[0]][location[1]] = value

  def ravel(self):
    return [room for row in self.map for room in row]

class Labyrinth:
  def __init__(self, size):
    self.size = size
    self.start_location = [randint(0, self.size-1), randint(0, self.size-1)]
    while True:
      self.map = Map(self.size)
      for i in range(self.size):
        for j in range(self.size):
          distance_fraction = ((abs(i - self.start_location[0])**2 + abs(j - self.start_location[1])**2)**0.5) / ((self.size-1) * 2**0.5)
          doors = []
          if i > 0:
            doors.append('north')
          if i+1 < self.size:
            doors.append('south')
          if j > 0:
            doors.append('west')
          if j+1 < self.size:
            doors.append('east')
          self.map.set_location(
            (i, j),
            choices(
              [NormalRoom, MerchantRoom, NebulaRoom],
              [0.8, 0.1 if distance_fraction > 0. else 0., 0.1 if distance_fraction > 0. else 0.]
            )[0](doors, distance_fraction)
          )
      if any([room.monsters for room in self.map.ravel()]) and any([isinstance(room, MerchantRoom) for room in self.map.ravel()]):
        break

  def get_room(self, location):
    return self.map.get_location(location)
