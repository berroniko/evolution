#!/usr/bin/env python
# coding: utf-8

# copy of version 25.7 evening was starting point for this one

ON_PYTHONISTA = True

import random
#from dataclasses import dataclass
from collections import defaultdict
import numpy as np
if not ON_PYTHONISTA:
	import matplotlib.pyplot as plt
# from abc import ABC, abstractmethod


X_SPAN = 10
Y_SPAN = 10
NR_HERBS_INIT = 30
NR_HERBIVORES_INIT = 20
NR_CYCLES = 500

VERBOSE = False


# ## map
# will become the central dictionary which holds all elements in their position. The position is defined as the tuple (x, y)

map = {(x, y): {} for x in range(0, X_SPAN) for y in range(0, Y_SPAN)}


def random_pos():
    return (random.randint(0, X_SPAN-1), random.randint(0, Y_SPAN-1))


def dist_pos(init_pos, steps, iteration = 0):
    '''defines new position a given nr of steps away'''
    if iteration > 20: steps = 1 
    # iteration is required to avoid endless loops if steps > available map-area
    dx = random.randint(0, steps)
    xn = init_pos[0] + dx * random.choice([-1, 1])
    yn = init_pos[1] + (steps-dx) * random.choice([-1, 1])
    if xn in range(0, X_SPAN) and yn in range(0, Y_SPAN):
    	new_pos = (xn, yn)
    else:
    	iteration += 1
    	new_pos = dist_pos(init_pos, steps, iteration)
    return new_pos


def move_conflict(first, second, themap):
    '''the first intends to take the position of the second,
    only the bigger one will survive'''
    if first.size > second.size:
        second.die('killed by move')
        themap[second.position][first.species] = first
        themap[first.position][first.species] = ''
        return True
    else: 
        first.die('lost move conflict')
        return False


class Element():
    _counter = 0
    inventory = []
    
    def __init__(self, coord, init_cycle = 0, parent_id = None):
        Element._counter += 1
        Element.inventory.append(self)
        self.id = Element._counter
        self.parent_id = parent_id
        self.alive = True
        self.species = type(self).__name__
        self.color = 'k'
        self._position: Tuple = coord
        self.init_cycle = init_cycle
        self.age = 0
        event_str = 'created at {}'.format(self._position)
        self.events = []  #{0: [event_str]}
        self.size = 1
        self._grow_rate = 1
        self.repro_rate = 3
        self.repro_dist = 1
        # self.repro_need = 2
        # self._move_rate = 0
        
    def __repr__(self):
        rep_str = '{} id{} {} age:{} size:{} pos{}'.format(
                    self.species, 
                    self.id, 
                    self.alive, 
                    self.age,
                    self.size,
                    self.position)
        return rep_str
    
    @property
    def counter():
        return Element._counter

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, new_position):
        self._position = new_position
        
    def old_event_tracker(self, text):
    	'append text to events dictionary in key age'
    	status = self.events.get(self.age, [])
    	status.append(text)
    	self.events[self.age] = status
    
    def event_tracker(self, text):
    	'adds tuple (age, text) to events'
    	self.events.append((self.age, text))
        
    def grow(self):
        self.size += self._grow_rate
    
    def die(self, text):
        self.alive = False
        global map
        map[self._position][self.species] = ''
        self.event_tracker(text)
        if VERBOSE:
	        print('{} with id{} died at age {}, size {}'.format(
	            self.species,
	            self.id,
	            self.age,
	            self.size)
	        )
        
    def move(self, dist, themap):
        old_pos = self._position
        new_pos = dist_pos(old_pos, dist)
        if VERBOSE:
            print('before old: ', themap[old_pos])
            print('before new: ', themap[new_pos])
        
        # check and solve potential conflict
        if themap[new_pos].get(self.species, '') == '':
            self._position = new_pos
            themap[self._position][self.species] = self
            themap[old_pos][self.species] = ''
            self.event_tracker('moved to {}'.format(self._position))
            
        else:
            move_conflict(self, themap[new_pos][self.species], themap)
        
        if VERBOSE:
            print('after old: ', themap[old_pos])
            print('after new: ', themap[new_pos])
             
    def cycle(self, themap, cycle_nr):
        if self.alive:
            self.age += 1
            self.grow()
            self.reproduce(themap, cycle_nr)
        else: pass


class Herb(Element):
    def __init__(self, coord, init_cycle, parent_id = None):
        
        super().__init__(coord, init_cycle, parent_id)
        self.color = 'g'
        
    def reproduce(self, themap, cycle_nr):
        if self.age % self.repro_rate == 0:
            new_pos = dist_pos(self._position, self.repro_dist)
            # check and solve potential conflict
            if (self.species not in themap[new_pos].keys() 
                or themap[new_pos][self.species] == ''):
                new_obj = Herb(new_pos, cycle_nr, self.id)
                themap[new_obj._position][new_obj.species] = new_obj
                #self.storage -= self.repro_need
                self.event_tracker('repro -> id {}'.format(new_obj.id))
                if VERBOSE:
	                print('New {} with id{}'.format(
	                            new_obj.species, new_obj.id))
            else:
                self.event_tracker('unsuccessfull repro')
        else: pass       


class Herbivore(Element):
    def __init__(self, coord, init_cycle, parent_id = None):
        self.storage = 3
        self._max_storage = 8
        self.need = 0.7
        
        super().__init__(coord, init_cycle)
        self._move_dist = 1
        self.color = 'b'
        self.repro_rate = 2
        self.repro_dist = 3
        self.repro_need = 4
    
    def eat(self, themap):
        # check available ressource
        try:
            available_res = themap[self._position]['Herb'].size
        except:
            available_res = 0
        # move if insufficient ressources at current position
        if available_res == 0: self.move(self._move_dist, themap)
        elif available_res <= self.need: 
            themap[self._position]['Herb'].size -= available_res
            self.storage += available_res
            self.move(self._move_dist, themap)
        else:  # enjoy all you can eat
            capa = self._max_storage - self.storage
            delta = capa if capa < available_res else available_res
            themap[self._position]['Herb'].size -= delta
            self.storage += delta   
            
    def reproduce(self, themap, cycle_nr):
        if (self.storage > 5
            and self.age % self.repro_rate == 0):
            new_pos = dist_pos(self._position, self.repro_dist)
            # check and solve potential conflict
            if themap[new_pos].get(self.species, '') == '':
                new_obj = Herbivore(new_pos, cycle_nr, self.id)
                themap[new_obj._position][new_obj.species] = new_obj
                self.storage -= self.repro_need
                self.event_tracker('repro -> id {}'.format(new_obj.id))
                if VERBOSE:
	                print('New {} with id{}'.format(
	                            new_obj.species, new_obj.id))
            else:
            	self.event_tracker('unsuccessfull repro')
        else: pass       
        
    def cycle(self, themap, cycle_nr):   
        if self.alive:
            self.storage -= self.need
            if self.storage < 0:
                self.die('starved')
                #self.event_tracker()
            else:
                self.age += 1
                self.eat(themap)
                if self.alive:
                	self.grow()
                	self.reproduce(themap, cycle_nr)
        else: pass


class Display():
    def __init__(self):
        # setup the figure and axes
        self.fig = plt.figure(figsize=(9, 6))
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        #self.ax1 = self.fig.add_subplot(121, projection='3d')
        #self.ax2 = self.fig.add_subplot(122, projection='3d')
        
    def show(self, the_map):
        u = []
        v = []
        w = []
        z = []

        for key,val in the_map.items():
            u.append(key[0])
            v.append(key[1])
            
            if 'Herb' in val.keys():
                w.append(val['Herb'].size)
            else:
                w.append(0)
            try:
                z.append(val['Herbivore'].size)
            except:
                z.append(0)
            
        bottom = np.zeros_like(w)
        width = depth = 0.8

        self.ax1.bar3d(u, v, bottom, width, depth, w, 
								shade=True, color='green')
        self.ax1.set_title('map')

        self.ax2.bar3d(u, v, bottom, width, depth, z, shade=True)
        self.ax2.set_title('Herbivore')

        plt.show()


# scatter plot data from cycles history
class DisplayCycles():
    # def __init__(self):
        
    def load(self, data):
        '''load the cycle data'''
        self.data = data
    
    def scatter_cycle_nr(self, nr):
        '''extract data of one cycle for scatter plot'''
        cycle = self.data[nr]
        #print(cycle)
        
        x = []
        y = []
        s = []
        c = []
        # shift to separate display of points on identical coordinates
        #shift_x = 0.1
        #shift_y = 0.1
        #dx = -shift_x
        # dy = -shift_y
        # for k, v in cycle.items():
        for el in Element.inventory:
            #dx += shift_x
            #dy += shift_y
            #for el in v:
            if el.alive:
                x.append(el.position[0])
                y.append(el.position[1])
                s.append(el.size)
                c.append(el.color)
            else: pass
       # print(x,y,s,c)
        self.cycle_values = [x, y, s, c]
        
    def show_cycle(self, nr, scale=1):
        self.scatter_cycle_nr(nr)
        x, y, s, c = self.cycle_values
        plt.scatter(x, y, s=[i*scale for i in s], c=c, alpha=0.5)
        plt.show()


# In[12]: Initialize environment  ----------------------

herbs = [Herb(random_pos(), 0) for i in range(NR_HERBS_INIT)]
for hb in herbs:
    map[hb.position][hb.species] = hb

herbivores = [Herbivore(random_pos(), 0) for i in range(NR_HERBIVORES_INIT)]
for h in herbivores:
    map[h.position][h.species] = h

# In[13]: CYCLE     ------------------------------------


cycles = []
for c in range(NR_CYCLES):
    for e in Element.inventory:
        e.cycle(map, c)
        #print(c, ': ', e)
        # flat list that contains the variables of all elements + nr of cycle
        dataset = vars(e).copy()
        dataset['cycle'] = c
        cycles.append(dataset)
if VERBOSE:
	print('results of final cycle')
	for e in Element.inventory:
		print(e)

# In[14]: DISPLAY RESULTS -----------------------------

if not ON_PYTHONISTA:
	disp = Display()
	disp.show(map)
	
	dc = DisplayCycles()
	dc.load(cycles)
	dc.show_cycle(4, scale = 15)
	

# DISPLAY AS TABLE.       ----------------------------

herbs=0
herb_age = 0
herbivore_alive = 0
herbivore_dead = 0
herbivore_age_a = 0
herbivore_age_d = 0
death_cause = defaultdict(int)

for h in Element.inventory:
	if VERBOSE:
		print('')
		print(h.id, h.species, ':', h.events)
		print('______________________________________________')
	if h.species == 'Herb':
		herbs += 1
		herb_age += h.age
	if h.species == 'Herbivore' and h.alive:
		herbivore_alive += 1
		herbivore_age_a += h.age
	if h.species == 'Herbivore' and not h.alive:
		herbivore_dead += 1
		herbivore_age_d += h.age
		cause = h.events[-1][1]
		death_cause[cause]+=1
		print(h.id, h.alive, h.events)
		
print('\n statistics \n')
print('{} herbs at avrg. age of {:.0f} \n'.format(herbs, herb_age/herbs))
try:
	av_age = herbivore_age_a/herbivore_alive
except:
	av_age = 'n.a.'
print('{} herbivores alive at avrg. age of {:.0f} \n'.format(herbivore_alive, av_age))
try:
	av_age = herbivore_age_d/herbivore_dead
except:
	av_age = 'n.a.'
print('{} herbivores died at avrg. age of {:.0f} \n'.format(herbivore_dead, av_age))
print(death_cause)



#print('Cycles \n', cycles)

# sort by id
#result = []
#if True:
#	for id_nr in range(Element._counter):
#		print('id_nr ------------------------------------------ ', id_nr,) 
#		for c in cycles:
#			print('c ',c)
#			if c['id'] == id_nr:
#				result.append(c)
	
#	print(result)


