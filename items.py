#!/usr/bin/env python3

from random import randint
from print import slow_print


class Item:
  def __eq__(self, other):
    if isinstance(other, Item):
      return self.name == other.name
    return NotImplemented

  def __hash__(self):
    return hash(self.name)

class Elixir(Item):
  def __init__(self):
    self.name = 'Elixir'
    self.price = 100
    self.not_usable_message = 'Your HP is full!'
    self.is_consumable = True

  def is_usable(self, player):
    return player.hp < player.max_hp

  def use(self, player):
    heal_amount = (2 * randint(1, 4)) + 2
    new_hp = min(player.max_hp, player.hp + heal_amount)
    slow_print(f'You heal {new_hp - player.hp} hp!')
    player.hp = new_hp
    slow_print(f'Current HP: {player.hp}/{player.max_hp}')

  def describe(self):
    return 'Consumable : +2d4+2 HP'

class SuperElixir(Item):
  def __init__(self):
    self.name = 'Super Elixir'
    self.price = 400
    self.not_usable_message = 'Your HP is full!'
    self.is_consumable = True

  def is_usable(self, player):
    return player.hp < player.max_hp

  def use(self, player):
    heal_amount = (4 * randint(1, 4)) + 4
    new_hp = min(player.max_hp, player.hp + heal_amount)
    slow_print(f'You heal {new_hp - player.hp} hp!')
    player.hp = new_hp
    slow_print(f'Current HP: {player.hp}/{player.max_hp}')

  def describe(self):
    return 'Consumable : +4d4+4 HP'

class MegaElixir(Item):
  def __init__(self):
    self.name = 'Mega Elixir'
    self.price = 1600
    self.not_usable_message = 'Your HP is full!'
    self.is_consumable = True

  def is_usable(self, player):
    return player.hp < player.max_hp

  def use(self, player):
    heal_amount = (6 * randint(1, 4)) + 6
    new_hp = min(player.max_hp, player.hp + heal_amount)
    slow_print(f'You heal {new_hp - player.hp} hp!')
    player.hp = new_hp
    slow_print(f'Current HP: {player.hp}/{player.max_hp}')

  def describe(self):
    return 'Consumable : +6d4+6 HP'
