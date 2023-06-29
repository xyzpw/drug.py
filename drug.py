#!/usr/bin/env python3

import time
import argparse
import math
from datetime import datetime

parse = argparse.ArgumentParser()
parse.add_argument("-p", help="Precision in decimals -- ineffective when using probability flag", type=int)
parse.add_argument("--unit", help="Time unit, default=hours. Options: (h)ours, (m)inutes, (s)econds", type=str)
parse.add_argument("--dose", help="Amount of chemical (units don't matter)", type=float)
parse.add_argument("--tmax", help="Tmax of the chemical", type=float)
parse.add_argument("--t12a", help="Absorption half-life of the chemical", type=float)
parse.add_argument("--t12", help="Half-life of the chemical", type=float)
parse.add_argument("--probability", action="store_true", help="Make results probability based")
parse.add_argument("--linear", action="store_true", help="Linear absorption/elimination (based on elimination constant and linear absorption rate)")
args = parse.parse_args()

args_list = vars(args)
input_values = ["dose", "tmax", "t12a", "t12"]

if args_list['probability'] and args_list['linear']:
    exit("Probability and linear cannot be active simultaneously")

def get_constant(half_life):
    constant = math.log(2) / half_life # get the constant absorption/elimination (ka/ke) rate | ln(2) / half-life
    return constant

def get_precision(num, precisionValue):
    if precisionValue == 0:
        return int(num)
    return math.floor(num * 10**precisionValue) / 10**precisionValue


class elimination_functions:
    def get_concentration(dose, time_since_tmax, half_life, prec):
        concentration = dose * 0.5**(time_since_tmax/half_life)
        return get_precision(concentration, prec)
    def get_probability(time_since_tmax, half_life):
        probability = 0.5**(time_since_tmax/half_life)
        return math.floor(probability * 100)
    def get_linear_concentration(dose, time_since_tmax, half_life, prec):
        ke = get_constant(half_life)
        concentration = dose - dose * time_since_tmax * ke
        return get_precision(concentration, prec)
class absorption_functions:
    def get_concentration(dose, time_since_dose, absorption_half_life, prec):
        concentration = dose - dose * 0.5**(time_since_dose/absorption_half_life)
        return get_precision(concentration, prec)
    def get_linear_concentration(dose, time_since_dose, peak, prec):
        concentration = (time_since_dose/peak) * dose
        return get_precision(concentration, prec)

# converting to seconds to make it easier to calculate with epoch
def convert_to_seconds(_time, _unit):
    _time = float(_time)
    _unit = _unit[0]
    match _unit:
        case "h":
            return _time * 3600
        case "m":
            return _time * 60
        case "s":
            return _time
        case None:
            return _time

def get_epoch():
    return time.time()

def main():
    tmax_epoch = 0
    if args_list['unit'] == None: args_list['unit'] = "h"
    if args_list['p'] == None: args_list['p'] = 0
    precisionInProperRange = args_list['p'] >= 0 and args_list['p'] <= 6
    precision = 0
    # set precision decimal range if it is in range (0 - 6)
    if precisionInProperRange:
        precision = float( args_list['p'] )
    tmaxed = False
    useLinear = args_list['linear']
    useProbability = args_list['probability']
    useDefault = (useLinear == False and useProbability == False)
    for i in input_values:
        if args_list.get(i) == None:
            if useDefault == False:
                if i == "t12a":
                    args_list[i] = 0
                    continue
                args_list[i] = float( input(f"{i.replace('t12', 'Half-life')}: ") )
            if useDefault:
                args_list[i] = float( input(f"{i.replace('t12a', 'Absorption half-life').replace('t12', 'Half-life')}: ") )
    startTime = get_epoch()
    adjusted_halflife = convert_to_seconds(args_list['t12'], args_list['unit'])
    adjusted_absorption_halflife = convert_to_seconds(args_list['t12a'], args_list['unit'])
    adjusted_tmax = convert_to_seconds(args_list['tmax'], args_list['unit'])
    #useLinear = args_list['linear']
    #useProbability = args_list['probability']
    #useDefault = (useLinear == False and useProbability == False)
    scriptStartDate = f"{datetime.now().month}/{datetime.now().day} {datetime.now().hour}:{datetime.now().minute}:{datetime.now().second}"
    # ansi code for linux only
    print(f"\n\033[31mStarting script at {scriptStartDate}\033[0m\n\n", end='')
    while True:
        time.sleep(0.25)
        timeSinceDose = get_epoch() - startTime
        timeSinceTmax = get_epoch() - tmax_epoch
        if useDefault:
            if tmaxed == False:
                if timeSinceDose >= adjusted_tmax:
                    tmaxed = True
                    tmax_epoch = get_epoch()
                    concentration = args_list['dose']
                concentration = absorption_functions.get_concentration(args_list['dose'], timeSinceDose, adjusted_absorption_halflife, precision)
                # "\033[2K" ansi code is only for linux
                print(f"\033[2KConcentration: {concentration}", end='\r', flush=True)
            if tmaxed:
                concentration = elimination_functions.get_concentration(args_list['dose'], timeSinceTmax, adjusted_halflife, precision)
                print(f"\033[2KConcentration: {concentration}", end='\r', flush=True)
        if useLinear:
            if tmaxed == False:
                if timeSinceDose >= adjusted_tmax:
                    tmaxed = True
                    tmax_epoch = get_epoch()
                    concentration = args_list['dose']
                concentration = absorption_functions.get_linear_concentration(args_list['dose'], timeSinceDose, adjusted_tmax, precision)
                print(f"\033[2KConcentration: {concentration}", end='\r', flush=True)
            if tmaxed:
                concentration = elimination_functions.get_linear_concentration(args_list['dose'], timeSinceTmax, adjusted_halflife, precision)
                print(f"\033[2KConcentration: {concentration}", end='\r', flush=True)
        if useProbability:
            if tmaxed == False:
                if timeSinceDose >= adjusted_tmax:
                    tmaxed = True
                    tmax_epoch = get_epoch()
                    concentration = args_list['dose']
                concentration = absorption_functions.get_linear_concentration(args_list['dose'], timeSinceDose, adjusted_tmax, precision)
                print(f"\033[2KConcentration: {concentration}", end='\r', flush=True)
            if tmaxed:
                concentration = elimination_functions.get_probability(timeSinceTmax, adjusted_halflife)
                print(f"\033[2KProbability of chemical remaining: {concentration}%", end='\r', flush=True)

try:
    main()
except KeyboardInterrupt:
    exit("\nTerminating script")
except Exception as e:
    exit("\n", e)

