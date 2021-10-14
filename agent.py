import math
import sys
import os
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
from lux.game_objects import City

DIRECTIONS = Constants.DIRECTIONS
game_state = None


def get_resource_tiles(game_state, height, width):
    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles


def get_empty_tiles(game_state, height, width):
    empty_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if not cell.has_resource() and not cell.citytile:
                empty_tiles.append(cell)
    return empty_tiles


def get_closest_resource_tile(unit, resource_tiles, player):
    closest_dist = math.inf
    closest_resource_tile = None
    # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal():
            continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium():
            continue
        dist = resource_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile
    return closest_resource_tile


def get_closest_city_tile(player, unit):
    closest_dist = math.inf
    closest_city_tile = None
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_city_tile = city_tile
    return closest_city_tile


def get_closes_empty_tile(unit, empty_tiles, player):
    closest_dist = math.inf
    closest_empty_tile = None
    for empty_tile in empty_tiles:
        dist = empty_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_empty_tile = empty_tile
    return closest_empty_tile


def get_city_lowes_fuel(player):
    fuel = []
    for k, city in player.cities.items():
        fuel.append(city.fuel)

    fuel.sort()

    return fuel[0]


def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])

    actions = []

    ### AI Code goes down here! ###
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles = get_resource_tiles(game_state, width, height)
    empty_tiles = get_empty_tiles(game_state, width, height)

    # for empty in empty_tiles:
    # actions.append(annotate.circle(empty.pos.x,empty.pos.y))

    # actions.append(annotate.sidetext(str(resource_tiles)))

    # we iterate over all our units and do something with them
    for unit in player.units:
        actions.append(annotate.text(unit.pos.x, unit.pos.y,
                       f"left:{unit.get_cargo_space_left()}", 42))
        if unit.is_worker() and unit.can_act():

            if unit.get_cargo_space_left() > 0:

                closest_resource_tile = get_closest_resource_tile(
                    unit, resource_tiles, player)
                if closest_resource_tile is not None:
                    actions.append(
                        unit.move(unit.pos.direction_to(closest_resource_tile.pos)))

            else:
                # try build city
                if get_city_lowes_fuel(player) > 300:
                    closest_empty_tile = get_closes_empty_tile(
                        unit, empty_tiles, player)
                    actions.append(annotate.circle(
                        closest_empty_tile.pos.x, closest_empty_tile.pos.y))
                    if closest_empty_tile is not None and not unit.pos == closest_empty_tile.pos:
                        actions.append(
                            unit.move(unit.pos.direction_to(closest_empty_tile.pos)))
                    elif unit.pos == closest_empty_tile.pos:
                        actions.append(annotate.x(unit.pos.x, unit.pos.y))
                        actions.append(unit.build_city())

                # if unit is a worker and there is no cargo space left, and we have cities, lets return to them
                if len(player.cities) > 0:
                    fuel = []
                    for k, city in player.cities.items():
                        fuel.append(city.fuel)

                    fuel.sort()
                    closest_dist = math.inf
                    closest_city_tile = None
                    for k, city in player.cities.items():
                        for city_tile in city.citytiles:
                            if city.fuel == fuel[0]:
                                dist = city_tile.pos.distance_to(unit.pos)
                                if dist < closest_dist:
                                    closest_dist = dist
                                    closest_city_tile = city_tile
                else:

                    closest_city_tile = get_closest_city_tile(player, unit)

                if closest_city_tile is not None:
                    move_dir = unit.pos.direction_to(closest_city_tile.pos)
                    actions.append(unit.move(move_dir))

    # for k, city in player.cities.items():
    #     if city.fuel > 300:
    #         for city_tile in city.citytiles:
    #             actions.append(annotate.circle(city_tile.pos.x, city_tile.pos.y))
    #             city_tile.build_worker()
    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))

    return actions
