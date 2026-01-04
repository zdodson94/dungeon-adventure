#!/usr/bin/env python3

from random import randint
from print import slow_print, slow_input, set_options
from save import save_game, edit_save_data
from copy import deepcopy
from collections import defaultdict
from math import floor
from monsters import Monster, BlackHole, health_per_con_point
from dungeon import NormalRoom, MerchantRoom, NebulaRoom, Map
from weapons import MeleeWeapon, StarShard
from spells import AttackSpell, SolarFlare
from items import Item, Elixir


level_to_xp_map = {1 : 0}
max_level = 10
for i in range(2, max_level+1):
  level_to_xp_map[i] = round(level_to_xp_map[i-1] + 10*(1.35**(i-2)))
attribute_points_per_level = 4

allowable_actions = [
  '(f)ight',
  '(l)ook/ta(l)k',
  '(m)ove',
  '(o)pen',
  '(i)nterface',
  '(q)uit'
]
action_shorthand_map = {
  'f' : 'fight',
  'l' : 'look',
  'm' : 'move',
  'o' : 'open',
  'i' : 'interface',
  'q' : 'quit'
}

allowable_battle_actions = ['attack', 'item', 'run']
battle_action_shorthand_map = {
  'a' : 'attack',
  'i' : 'item',
  'r' : 'run'
}

allowable_movement_directions = ['north', 'south', 'east', 'west', 'return']
movement_shorthand_map = {
  'n' : 'north',
  's' : 'south',
  'e' : 'east',
  'w' : 'west',
  'r' : 'return'
}

def quit_game(*args):
  slow_print('You cease your endeavor.')
  exit()

class MovementError(Exception):
  def __init__(self, message):
    self.message = message
    super().__init__(self.message)
  def __str__(self):
    return f"{self.message}"

class PlayerInventory:
  def __init__(self):
    self.items = defaultdict(int)

  def add_item(self, item, number=1):
    self.items[item] += number

  def remove_item(self, item):
    if self.items[item] == 1:
      self.items.pop(item)
    else:
      self.items[item] -= 1

  def get_item_by_enumeration(self, num):
    if 1 <= num <= len(self.items):
      return list(self.items.keys())[num-1]
    else:
      return None

  def print_item_enumeration_and_amount(self):
    for i, (item, quantity) in enumerate(self.items.items()):
      slow_print(f' - [{i+1}] : {item.name} (Amount: {quantity})')

  def print_item_enumeration_description_and_amount(self):
    for i, (item, quantity) in enumerate(self.items.items()):
      slow_print(f' - [{i+1}] : {item.name} ({item.describe()}) (Amount: {quantity})')

  def print_item_enumeration_amount_and_price(self):
    for i, item in enumerate(self.items):
      slow_print(f' - [{i+1}] : {item.name} (Quantity: {self.items[item]}) ({item.price} Fe)')

class Player:
  def __init__(self, start_location):
    self.iron = 0
    self.inventory = PlayerInventory()
    self.inventory.add_item(Elixir(), number=3)
    self.weapons = set()
    self.spells = set()
    self.actions = {
      'fight'     : self.battle,
      'look'      : self.look_around,
      'move'      : self.move,
      'open'      : self.open,
      'interface' : self.interface,
      'quit'      : quit_game
    }
    self.battle_actions = {
      'attack' : self.attack_action,
      'item'   : self.use_item,
      'run'    : self.run
    }
    self.attributes = {
      'LUM' : 10,
      'SIZ' : 10,
      'VEL' : 10
    }
    self.level = slow_input(
      f'Player starting level [1 - {max_level}]:',
      int,
      allowable_inputs=list(range(1, max_level+1))
    )
    self.experience_points = level_to_xp_map[self.level]
    self.location = start_location
    self.map = None
    self.attribute_points = attribute_points_per_level * (self.level - 1)

  def get_attribute_modifier(self, attr):
    return floor((self.attributes[attr] - 10) / 2)

  def battle(self, labyrinth):
    room = labyrinth.get_room(self.location)
    if room.monsters:
      slow_print(f'You face {len(room.monsters)} monster(s)!')
      for monster in room.monsters:
        slow_print(f' - {monster.name} ({monster.hp}/{monster.max_hp} HP)')
      turn_order = sorted([self] + room.monsters, key=lambda x: x.roll_initiative())[::-1]
      while room.monsters:
        while any(entity.hp == 0 for entity in turn_order):
          for i in range(len(turn_order)):
            if turn_order[i].hp == 0:
              turn_order.pop(i)
              break
        for entity in turn_order:
          if entity.hp > 0:
            if isinstance(entity, Monster):
              entity.attack(self)
            else:
              if self.battle_actions[
                slow_input(
                  f'What would you like to do? [(a)ttack, (i)tem, (r)un]:',
                  shorthand_map=battle_action_shorthand_map,
                  allowable_inputs=allowable_battle_actions
                )
              ](labyrinth, room.monsters) == 'escaped':
                self.check_level_up()
                return
      self.check_level_up()
    elif isinstance(room, MerchantRoom):
      room.antagonized = True
      slow_print('You challenge the ring of light.')
      slow_print('Suddenly you are small, and you gaze up at something your mind cannot fathom...')
      room.monsters = [BlackHole()]
      room.items = None
      self.battle(labyrinth)
      if not room.monsters:
        room.not_defeated = False
    else:
      slow_print('There is nothing to fight...')

  def action(self, labyrinth):
    if self.map is None:
      self.map = Map(labyrinth.size, '?')
    room = labyrinth.get_room(self.location)
    if isinstance(room, NormalRoom):
      if (not room.monsters) and (not room.treasure):
        self.map.set_location(self.location, 'X')
      elif room.monsters:
        self.map.set_location(self.location, 'D')
      elif room.treasure:
        self.map.set_location(self.location, 'C')
    elif isinstance(room, MerchantRoom):
      self.map.set_location(self.location, 'M')
    elif isinstance(room, NebulaRoom):
      self.map.set_location(self.location, 'N')
    self.actions[
      slow_input(
        f'What would you like to do next? [{", ".join(allowable_actions)}]: ',
        shorthand_map=action_shorthand_map,
        allowable_inputs=self.actions.keys()
      )
    ](labyrinth)

  def open(self, labyrinth):
    room = labyrinth.get_room(self.location)
    if not room.monsters:
      if room.treasure:
        slow_print(f'There are {len(room.treasure)} chest(s) in the room. You start opening...')
        while room.treasure:
          chest = room.treasure.pop(0)
          slow_print(f'You open a {chest.size} chest and find {chest.iron} iron!')
          if chest.item:
            slow_print(f'You also find {chest.item.name} inside!')
            self.inventory.add_item(chest.item)
          self.iron += chest.iron
      else:
        slow_print('There are no chests in the room.')
    else:
      slow_print('Enemies block the treasure...')

  def look_around(self, labyrinth):
    room = labyrinth.get_room(self.location)
    if isinstance(room, MerchantRoom):
      if room.not_defeated and not room.antagonized:
        self.shop(room)
      elif room.antagonized:
        self.battle(labyrinth)
      else:
        room.describe(self)
    else:
      room.describe(self)


  def use_item(self, *args):
    if self.inventory.items:
      slow_print('Which item would you like to use? [enter # of item or (r)eturn]')
      self.inventory.print_item_enumeration_description_and_amount()
      idx = slow_input(
        '',
        shorthand_map={'r' : 'return'},
        allowable_inputs=[str(i) for i in range(1, len(self.inventory.items)+1)] + ['return']
      )
      if idx == 'return':
        return
      else:
        idx = int(idx)
      item = self.inventory.get_item_by_enumeration(idx)
      if isinstance(item, Item):
        if item.is_usable(self):
          item.use(self)
          if item.is_consumable:
            self.inventory.remove_item(item)
        else:
          slow_print(item.not_usable_message)
      else:
        slow_print('Item not available!')
    else:
      slow_print('Your bag is empty!')

  def move(self, labyrinth):
    room = labyrinth.get_room(self.location)
    if not room.monsters:
      try:
        self.change_room(labyrinth)
      except MovementError:
        slow_print("You can't go that way!")
        self.action(labyrinth)
    else:
      slow_print('Enemies block your path!')
      escape = slow_input('Would you like to attempt to escape? [y/n]', allowable_inputs=['y', 'n'])
      if escape == 'y':
        if self.escape_check(room.monsters):
          slow_print('You escaped!')
          self.change_room(labyrinth)
        else:
          slow_print('You could not escape!')
          self.battle(labyrinth)

  def change_room(self, labyrinth):
    slow_print('The following doors are available [enter direction or (r)eturn]:')
    for door in labyrinth.get_room(self.location).doors:
      slow_print(f'   - a door to the ({door[0]}){door[1:]}')
    loc = list(self.location)
    direction = slow_input(
      'What direction do you go?',
      shorthand_map=movement_shorthand_map,
      allowable_inputs=allowable_movement_directions
    )
    if direction == 'south':
      if self.location[0]+1 < labyrinth.map.size:
        loc[0] += 1
        slow_print(f'You head south and enter the next room...')
      else:
        raise MovementError("Cannot move south!")
    elif direction == 'west':
      if self.location[1] > 0:
        loc[1] -= 1
        slow_print(f'You head west and enter the next room...')
      else:
        raise MovementError("Cannot move west!")
    elif direction == 'east':
      if self.location[1]+1 < labyrinth.map.size:
        loc[1] += 1
        slow_print(f'You head east and enter the next room...')
      else:
        raise MovementError("Cannot move east!")
    elif direction == 'north':
      if self.location[0] > 0:
        loc[0] -= 1
        slow_print(f'You head north and enter the next room...')
      else:
        raise MovementError("Cannot move north!")
    elif direction == 'return':
      slow_print('You do not move.')
      return
    self.location = tuple(loc)
    labyrinth.get_room(self.location).describe(self)

  def interface(self, *args):
    while True:
      choice = slow_input(
        'What would you like to do? [(c)heck, (u)se, (a)ssign, (s)ave, (d)ata, (o)ptions, (r)eturn]',
        shorthand_map={'c' : 'check', 'u' : 'use', 'a' : 'assign', 's' : 'save', 'd' : 'data', 'o' : 'options', 'r' : 'return'},
        allowable_inputs=['check', 'use', 'assign', 'save', 'data', 'options', 'return']
      )
      if choice == 'check':
        self.check(*args)
      elif choice == 'use':
        self.use_item(*args)
      elif choice == 'assign':
        self.assign_attribute_points(*args)
      elif choice == 'save':
        self.save_game(*args)
      elif choice == 'data':
        edit_save_data(*args)
      elif choice == 'options':
        set_options(*args)
      elif choice == 'return':
        break

  def check(self, *args):
    while True:
      choice = slow_input(
        'What would you like to check? [(s)tats, (i)tems, (m)ap, (a)ttacks, (r)eturn]',
        shorthand_map={'s' : 'stats', 'i' : 'items', 'm' : 'map', 'a' : 'attacks', 'r' : 'return'},
        allowable_inputs=['stats', 'items', 'map', 'attacks', 'return']
      )
      if choice == 'stats':
        slow_print('STATS')
        slow_print(f' - Level : {self.level}')
        if self.level < max_level:
          slow_print(f' - XP    : {self.experience_points}/{level_to_xp_map[self.level+1]}')
        else:
          slow_print(f' - XP    : {self.experience_points}')
        slow_print(f' - AP    : {self.attribute_points}')
        slow_print(f' - HP    : {self.hp}/{self.max_hp}')
        slow_print(f' - Iron  : {self.iron}')
        slow_print('ATTRIBUTES')
        for attr, val in self.attributes.items():
          slow_print(f' - {attr} : {val:>2d} ({self.get_attribute_modifier(attr):+d})')
      elif choice == 'items':
        if self.inventory.items:
          slow_print('ITEMS')
          self.inventory.print_item_enumeration_description_and_amount()
        else:
          slow_print('Your bag is empty.')
      elif choice == 'map':
        if self.map is not None:
          slow_print('MAP')
          tmp_map = deepcopy(self.map)
          tmp_map.set_location(self.location, '*')
          slow_print(f'┌{"───┬" * (tmp_map.size - 1)}───┐')
          for i in range(tmp_map.size):
            slow_print(f'│ {" ┆ ".join([c for c in tmp_map.map[i]])} │')
            if i+1 == tmp_map.size:
              slow_print(f'└{"───┴" * (tmp_map.size - 1)}───┘')
            else:
              slow_print(f'├{"───┼" * (tmp_map.size - 1)}───┤')
        else:
          slow_print('Your map is empty.')
      elif choice == 'attacks':
        if isinstance(self, Fighter):
          slow_print('WEAPONS')
          for weapon in self.weapons:
            slow_print(f' - {weapon.name}')
          slow_print(f'EQUIPPED WEAPON : {self.equipped_weapon.name}.')
        elif isinstance(self, Mage):
          slow_print('SPELLS')
          for spell in self.spells:
            slow_print(f' - {spell.name}')
      elif choice == 'return':
        break

  def assign_attribute_points(self, *args):
    if self.attribute_points > 0:
      while self.attribute_points > 0:
        slow_print('Current attributes:')
        for attr, val in self.attributes.items():
          slow_print(f' - {attr} : {val:>2d} ({self.get_attribute_modifier(attr):+d})')
        slow_print(f'You have {self.attribute_points} AP.')
        choice = slow_input(
          'What attribute would you like to increase? [(l)um, (s)iz, (v)el, (f)inish]',
          shorthand_map={'l' : 'lum', 's' : 'siz', 'v' : 'vel', 'f' : 'finish'},
          allowable_inputs=['lum', 'siz', 'vel', 'finish']
        )
        if choice == 'finish':
          break
        choice = choice.upper()
        amount = slow_input(
          f'How many points to you assign to {choice}? [0 - {self.attribute_points}]',
          int,
          allowable_inputs=list(range(self.attribute_points+1))
        )
        self.attributes[choice] += amount
        self.attribute_points -= amount
        if choice == 'SIZ':
          self.hp += amount * health_per_con_point
        slow_print(f'{choice} is now {self.attributes[choice]} ({self.get_attribute_modifier(choice):+d}). You have {self.attribute_points} points left.')
      self.assign_max_hp()
    else:
      slow_print('You do not have any points to assign!')

  def shop(self, room: MerchantRoom):
    slow_print('You approach the warping light...')
    while True:
      buy_or_sell = slow_input(
        'Would you like to do? [(b)uy/(s)ell/(l)eave]',
        shorthand_map={'b' : 'buy', 's' : 'sell', 'l' : 'leave'},
        allowable_inputs=['buy', 'sell', 'leave']
      )
      if buy_or_sell != 'leave':
        if buy_or_sell == 'buy':
          slow_print(f'Current iron: {self.iron} Fe')
          slow_print('The following items are available:')
          for i, item in enumerate(room.items):
            slow_print(f' - [{i+1}] : {item.name} ({item.describe()}) ({item.price} Fe)')
          while True:
            choice = slow_input(
              'Which would you like to buy? [# or (r)eturn]',
              shorthand_map={'r' : 'return'},
              allowable_inputs=[str(i+1) for i in range(len(room.items))] + ['return']
            )
            if choice != 'return':
              try:
                choice = int(choice)-1
              except:
                slow_print('Unrecognized command!')
                continue
              item = room.items[choice]
              if isinstance(item, MeleeWeapon) and (not isinstance(self, Fighter)):
                slow_print('You cannot buy weapons...')
                continue
              if isinstance(item, AttackSpell):
                if not isinstance(self, Mage):
                  slow_print('You cannot buy spells...')
                  continue
                elif item in self.spells:
                  slow_print(f'You already know {item.name}!')
                  continue
                elif item in self.inventory.items:
                  slow_print(f'You have already purchased {item.name}!')
                  continue
              if 0 <= choice < len(room.items):
                if self.iron >= item.price:
                  num_can_afford = floor(self.iron / item.price)
                  quantity = slow_input(f'How many would you like to buy? [0 - {num_can_afford}]', int, allowable_inputs=list(range(num_can_afford+1))) if item.is_consumable else 1
                  if quantity == 0:
                    continue
                  if self.iron >= item.price * quantity:
                    slow_print(f'You purchase {str(quantity) + " " if item.is_consumable else ""}{item.name} for {item.price * quantity} Fe...')
                    self.inventory.add_item(item, number=quantity)
                    self.iron -= item.price * quantity
                    slow_print(f'Remaining iron: {self.iron}')
                    continue
                else:
                  slow_print("You don't have enough iron for that!")
                  continue
              slow_print('That item is not available!')
            else:
              break
        elif buy_or_sell == 'sell':
          if not self.inventory.items:
            slow_print("You don't have anything to sell!")
            continue
          while True:
            slow_print('What would you like to sell? [# or (r)eturn]')
            self.inventory.print_item_enumeration_amount_and_price()
            choice = slow_input(
              '',
              shorthand_map={'r' : 'return'},
              allowable_inputs=[str(i+1) for i in range(len(self.inventory.items))] + ['return']
            )
            if choice != 'return':
              try:
                choice = int(choice)
              except:
                slow_print('Unrecognized command!')
                continue
              if 1 <= choice <= len(self.inventory.items):
                item = self.inventory.get_item_by_enumeration(choice)
                if isinstance(item, MeleeWeapon) and isinstance(self, Fighter):
                  if sum(v if isinstance(k, MeleeWeapon) else 0 for k, v in self.inventory.items.items()) == 1:
                    slow_print("You can't sell your last weapon!")
                    continue
                slow_print(f'You sell {item.name} for {item.price} Fe...')
                self.iron += item.price
                self.inventory.remove_item(item)
                slow_print(f'Iron: {self.iron}')
              else:
                slow_print('That item is not available!')
                continue
            else:
              break
      else:
        break
    slow_print('The ring of light dims and flickers...')
    self.weapons = set()
    for item in self.inventory.items:
      if isinstance(item, MeleeWeapon):
        if item not in self.weapons:
          self.weapons.add(item)
      elif isinstance(item, AttackSpell):
        if item not in self.spells:
          slow_print(f'You learn to cast {item.name}!')
          self.spells.add(item)
    if isinstance(self, Fighter):
      if self.equipped_weapon not in self.weapons:
        self.equipped_weapon = list(self.weapons)[0]
        slow_print(f'Your equipped weapon has been changed to {self.equipped_weapon.name}.')
    while any([isinstance(i, AttackSpell) for i in self.inventory.items]):
      for item in self.inventory.items:
        if isinstance(item, AttackSpell):
          self.inventory.remove_item(item)
          break

  def run(self, labyrinth, monsters):
    if self.escape_check(monsters):
      slow_print('You escaped!')
      self.change_room(labyrinth)
      return 'escaped'
    else:
      slow_print("You failed to escape!")

  def escape_check(self, monsters):
    avg_monster_initiative = sum(monster.roll_initiative() for monster in monsters) / len(monsters)
    return self.roll_initiative() >= avg_monster_initiative

  def check_level_up(self):
    leveled_up = False
    while True:
      if self.level < max_level:
        if self.experience_points >= level_to_xp_map[self.level+1]:
          self.level += 1
          self.attribute_points += attribute_points_per_level
          slow_print(f'You leveled up to level {self.level}!')
          leveled_up = True
        else:
          break
      else:
        break
    if leveled_up:
      slow_print(f'You have {self.attribute_points} attribute points.')

  def save_game(self, labyrinth):
    save_game(self, labyrinth)

  def get_AC(self):
    return 10 + self.get_attribute_modifier('VEL')

  def roll_initiative(self):
    return randint(1, 20) + self.get_attribute_modifier('VEL')

  def assign_max_hp(self):
    self.max_hp = self.attributes['SIZ'] * health_per_con_point

class Fighter(Player):
  def __init__(self, start_location):
    super().__init__(start_location)
    self.attributes['LUM'] += 2
    self.attributes['SIZ'] += 2
    self.attributes['VEL'] += 2
    self.hp = self.attributes['SIZ'] * health_per_con_point
    self.assign_max_hp()
    self.inventory.add_item(StarShard())
    self.weapons.add(StarShard())
    self.equipped_weapon = list(self.weapons)[0]

  def attack_action(self, labyrinth, monsters):
    if len(monsters) > 1:
      slow_print('Which enemy do you attack? ')
      for i, monster in enumerate(monsters):
        if monster.hp > 0:
          slow_print(f' - [{i+1}] : {monster.name} ({monster.hp}/{monster.max_hp} HP)')
      idx = slow_input('', int, allowable_inputs=list(range(1, len(monsters)+1)))
    else:
      idx = 1
    _monster = monsters[idx-1]
    self.attack(_monster)
    if _monster.hp <= 0:
      slow_print(f'{_monster.name} has died!')
      self.experience_points += _monster.xp_worth
      if _monster.iron:
        slow_print(f'You pick up {_monster.iron} iron...')
        self.iron += _monster.iron
      monsters.pop(idx-1)

  def attack(self, monster):
    if randint(1, 20) + self.get_attribute_modifier('LUM') >= monster.AC:
      damage = self.equipped_weapon.roll_damage() + self.equipped_weapon.attack_bonus + self.get_attribute_modifier('LUM')
      monster.hp = max(0, monster.hp - damage)
      slow_print(f'You inflict {damage} damage on {monster.name} (HP : {monster.hp}/{monster.max_hp})!')
    else:
      slow_print(f'You missed {monster.name}...')

class Mage(Player):
  def __init__(self, start_location):
    super().__init__(start_location)
    self.attributes['LUM'] += 6
    self.attributes['SIZ'] -= 2
    self.attributes['VEL'] += 2
    self.hp = self.attributes['SIZ'] * health_per_con_point
    self.assign_max_hp()
    self.spells.add(SolarFlare())

  def attack_action(self, labyrinth, monsters):
    slow_print('What spell do you use?')
    for i, spell in enumerate(self.spells):
      slow_print(f' - [{i+1}] : {spell.name}')
    chosen_spell = list(self.spells)[slow_input('', int, allowable_inputs=list(range(1, len(self.spells)+1)))-1]
    if chosen_spell.range == 'single':
      if len(monsters) > 1:
        slow_print('Which enemy do you attack?')
        for i, monster in enumerate(monsters):
          if monster.hp > 0:
            slow_print(f' - [{i+1}] : {monster.name} ({monster.hp}/{monster.max_hp} HP)')
        idx = slow_input('', int, allowable_inputs=list(range(1, len(monsters)+1)))
      else:
        idx = 1
      self.attack([monsters[idx-1]], chosen_spell)
    elif chosen_spell.range == 'multiple':
      self.attack(monsters, chosen_spell)
    while any([monster.hp <= 0 for monster in monsters]):
      for i, monster in enumerate(monsters):
        if monster.hp <= 0:
          slow_print(f'{monster.name} has died!')
          self.experience_points += monster.xp_worth
          if monster.iron:
            slow_print(f'You pick up {monster.iron} iron...')
            self.iron += monster.iron
          monsters.pop(i)

  def attack(self, monsters, spell):
    damage = spell.roll_damage() + self.get_attribute_modifier('LUM')
    for monster in monsters:
      if randint(1, 20) + self.get_attribute_modifier('LUM') >= monster.AC:
        slow_print(f'You inflict {damage} damage on {monster.name}!')
        monster.hp = max(0, monster.hp - damage)
      else:
        slow_print(f'You missed {monster.name}...')
