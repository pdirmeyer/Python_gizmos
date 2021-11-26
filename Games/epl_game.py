#############################################################
##### Simulates a pseudo-Premier League season
##### Scoring controlled by 3 ratings per team
##### Home team advantage not instituted
#############################################################

import sys
import numpy as np
import pandas as pd
import random
import matplotlib.pyplot as plt
# random.seed(a=3) # For testing reproducability
from operator import itemgetter
from scipy.optimize import curve_fit

##### Set up arrays for stats, etc.

# Fill all the initial ratings for teams, and their names
nteams = 20
teams = ("Powderdamp", "Loudemouth", "Borussia Albion", "Chumley United", "Aberabbit", 
         "Hilary", "Unicorn Castle", "Neverborough", "Baconbury", "Sputterstead Village",
         "Moncester City", "Spleenwich", "Blokeham City", "Blokeham FC", "Geordie Abbey",
         "Umbridge", "Kiddingshire Cold Pudding", "Bangerford", "North Chop United",
         "Hopechester Munters")
abbrs = ("POW", "LOU", "BA", "CU", "ABE", 
         "HIL", "UC", "NEV", "BAC", "SV",
         "MON", "SPL", "BC", "BFC", "GA", 
         "UMB", "KCP", "BAN", "NCU", "HM")
realt = ("ARS", "BOU", "BHA", "BUR", "CAR", 
         "CHE", "CP", "EVE", "FUL", "HUD",
         "LC", "LIV", "MC", "MU", "NEW", 
         "SOU", "TOT", "WAT", "WHU", "WOL")
tcount = list(range(nteams))
tcolor1 = ("#C81B17", "#EF0107", "#0057B8", "#6C1D45", "#0070B5", 
           "#034694", "#1B458F", "#003399", "#CC0000", "#0E63AD", 
           "#003090", "#C8102E", "#6CABDD", "#DA291C", "#241F20", 
           "#130C0E", "#132257", "#FBEE23", "#7A263A", "#FDB913")
tcolor2 = ("#EFDBB2", "#DB0007", "#EEEEEE", "#99D6EA", "#D11524", 
           "#D1D3D4", "#C4122E", "#003399", "#000000", "#FFFFFF", 
           "#FDBE11", "#FFFFFF", "#1C2C5B", "#FBE122", "#41B6E6", 
           "#D71920", "#FFFFFF", "#ED2127", "#1BB1E7", "#231F20")
orate = (1, 2, 2, 3, 3, 1, 2, 3, 3, 3,
         2, 1, 1, 2, 2, 2, 1, 2, 3, 2)
drate = (1, 3, 3, 3, 3, 1, 2, 1, 2, 3,
         2, 1, 1, 1, 2, 3, 1, 3, 2, 3)
krate = (3, 2, 2, 1, 3, 2, 2, 2, 2, 3,
         2, 2, 2, 1, 2, 2, 2, 3, 2, 2)


# Probabilities for scoring
shotp = (0.33, 0.37, 0.42, 0.49, 0.59) # index is (drate - orate + 2)
targp = (0.29, 0.33, 0.38)             # index is (3 - orate)
keepp = (0.24, 0.31, 0.36)             # index is (krate - 1)
pertmag = 0.06                         # Allows for drift over time

# Function fit thru probabilities y = a - b*(1-exp(-k*x))
def func_epl(x, a, b, k):
    return a - b/k * (1 - np.exp(-k * x))
xdata = (0.0, 1.0, 2.0, 3.0, 4.0)
popt, pcov = curve_fit(func_epl, xdata, shotp)
co_shot = popt  # a, b and k to best match shotp
xdata = (0.0, 1.0, 2.0)
popt, pcov = curve_fit(func_epl, xdata, targp)
co_targ = popt  # a, b and k to best match targp    
xdata = (0.0, 1.0, 2.0)
popt, pcov = curve_fit(func_epl, xdata, keepp)
co_keep = popt  # a, b and k to best match keepp 
#print(popt)
#bestfit = [0] * 3
#for i in range(0,3):
#    bestfit[i] = func_epl(i, *popt)
#print(bestfit)
#sys.exit()

# Set up perturbations to team ratings that can evolve
# in a random Brownian manner thru the season
opert = [0] * 20
dpert = [0] * 20
kpert = [0] * 20 


##### Generate schedule array

# Create empty arrays to house schedule    
weeks = (nteams-1) * 2
games = int(nteams/2)
week_home = [[0] * games for i in range(weeks)]
week_away = [[0] * games for i in range(weeks)]
    
# Set up first week of pattern
week_home[0] = list(range(0, games))
week_away[0] = list(range(nteams-1, games-1, -1))
#print("Week: 1")
#print(week_home[0])
#print(week_away[0])
#print(" --- ")

# Loop thru weeks, keep team 0 in same slot, rotate others thru
for week in range(0, weeks-1):
#    print(" ".join(["Week:",str(week + 2)]))

# Clear out the week's lists of teams
    new_home, new_away = [], []
#    new_away = []

# Set up the teams in each game by moving slots from previous week
# Game #1
    new_home.append(week_home[week][0])
    new_away.append(week_home[week][1])

# Games #2-#9
    for game in range(1, games-1):
        new_home.append(week_home[week][game+1])
        new_away.append(week_away[week][game-1])

# Game #10
    new_home.append(week_away[week][9])
    new_away.append(week_away[week][8])

#    print(new_home)
#    print(new_away)
#    print(" --- ")
        
# Place new week's pairings into the schedule matrix        
    week_home[week+1] = new_home
    week_away[week+1] = new_away
#    print(week_home) 

# Invert home and away slots every other week     
for week in range(0, weeks):
    if week % 2 == 0:
        new_away = week_home[week]
        week_home[week] = week_away[week]
        week_away[week] = new_away
      
##### Keep track of stats and standings
# Set up table
table_w = [0] * nteams
table_d = [0] * nteams
table_l = [0] * nteams
table_gf = [0] * nteams
table_ga = [0] * nteams
table_gd = [0] * nteams
table_pts = [0] * nteams
table_rank = [0] * nteams

# Keep track of evolution of stats through season for each team
weekly_rank = [[0] * nteams for i in range(weeks)]
weekly_pts = [[0] * nteams for i in range(weeks)]
last_five = [""] * nteams


################################################################
# Game play
# 30 3-minute intervals (15 per half)
# Each interval has a shot probability (shotp)
# If there is a shot, it has an on-target prob (targp)
# If shot is on goal, it has prob to get past the keeper (keepp)
print(" ")

# Loop through weeks
for week in range(0, weeks):
    print("Week: ",int(week+1))

# Update perturbed ratings    
    ocafe = [sum(i) for i in zip(orate,opert)]
    dcafe = [sum(i) for i in zip(drate,dpert)]
    kcafe = [sum(i) for i in zip(krate,kpert)]

# Loop through games
# Shuffle sequence for fun    
    gseq = [i for i in range(games)]
    random.shuffle(gseq)
    for game in range(0, games):

# Set up bookkeeping for game
        home_team = week_home[week][gseq[game]]
        away_team = week_away[week][gseq[game]]
#        home_shotp = shotp[int(drate[away_team]-orate[home_team]+2)]
        home_shotp = func_epl(dcafe[away_team]-ocafe[home_team]+2, *co_shot)
#        home_targp = targp[int(3-orate[home_team])]
        home_targp = func_epl(3-ocafe[home_team], *co_targ)
#        home_keepp = keepp[krate[away_team]-1]
        home_keepp = func_epl(kcafe[away_team]-1, *co_keep)
#        away_shotp = shotp[int(drate[home_team]-orate[away_team]+2)]
        away_shotp = func_epl(dcafe[home_team]-ocafe[away_team]+2, *co_shot)
#        away_targp = targp[int(3-orate[away_team])]
        away_targp = func_epl(3-ocafe[away_team], *co_targ)
#        away_keepp = keepp[krate[home_team]-1]
        away_keepp = func_epl(kcafe[home_team]-1, *co_keep)

        home_goals_string = abbrs[home_team] + ":"
        away_goals_string = abbrs[away_team] + ":"
        home_shotc, home_targc, home_score = 0, 0, 0
        away_shotc, away_targc, away_score = 0, 0, 0
        print(" ")
        print("Game",int(game+1),"-",teams[home_team],"vs",teams[away_team])

# Loop through the time intervals        
        for interval in range(0, 30):
            cheer = 0

# Does home team score? (Having first chance is home field advantage)          
            if (random.random() < home_shotp):
                home_shotc += 1 
                if (random.random() < home_targp):
                    home_targc += 1
                    if (random.random() < home_keepp):
                        home_score += 1
                        cheer = 1
                        goal_time = int(random.uniform(0,3))+interval*3+1
                        home_goals_string += " " + str(goal_time) + "'" 
#                        print(f"{teams[home_team]} @ {goal_time}'")

# If not, does away team score?     
            if (random.random() < away_shotp) and (cheer == 0):
                away_shotc += 1 
                if (random.random() < away_targp):
                    away_targc += 1
                    if (random.random() < away_keepp):
                        away_score += 1
                        goal_time = int(random.uniform(0,3))+interval*3+1
                        away_goals_string += " " + str(goal_time) + "'"
#                        print(f"{teams[away_team]} @ {goal_time}'")

        print("FT:",teams[home_team],home_score,"-",away_score,teams[away_team])
        if (home_score > 0):
            if (away_score > 0):
                print("> " + home_goals_string + "; " + away_goals_string)
            else:
                print("> " + home_goals_string)
        else:
            if (away_score > 0):
                print("> " + away_goals_string)
            else:
                print("> ")


##### Match over - update table stats 
        if (home_score > away_score):
            table_w[home_team] += 1
            last_five[home_team] = "W" + last_five[home_team] 
            if (len(last_five[home_team]) > 5):
                last_five[home_team] = last_five[home_team][:5]
            table_l[away_team] += 1
            last_five[away_team] = "L" + last_five[away_team]
            if (len(last_five[away_team]) > 5):
                last_five[away_team] = last_five[away_team][:5]
        elif (home_score < away_score):
            table_w[away_team] += 1
            last_five[away_team] = "W" + last_five[away_team]
            if (len(last_five[away_team]) > 5):
                last_five[away_team] = last_five[away_team][:5]
            table_l[home_team] += 1
            last_five[home_team] = "L" + last_five[home_team]
            if (len(last_five[home_team]) > 5):
                last_five[home_team] = last_five[home_team][:5]        
        else:
            table_d[home_team] += 1
            last_five[home_team] = "D" + last_five[home_team]
            if (len(last_five[home_team]) > 5):
                last_five[home_team] = last_five[home_team][:5]        
            table_d[away_team] += 1
            last_five[away_team] = "D" + last_five[away_team]
            if (len(last_five[away_team]) > 5):
                last_five[away_team] = last_five[away_team][:5]
        table_gf[home_team] += home_score
        table_ga[away_team] += home_score
        table_gf[away_team] += away_score
        table_ga[home_team] += away_score
        table_gd[home_team] = table_gf[home_team] - table_ga[home_team]
        table_gd[away_team] = table_gf[away_team] - table_ga[away_team]
        table_pts[home_team] = 3 * table_w[home_team] + table_d[home_team]
        table_pts[away_team] = 3 * table_w[away_team] + table_d[away_team]
    print(" ")    
    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
#############################################################

##### Week over - updated the table and print
    table_tup = zip(teams,table_w,table_d,table_l,table_pts,table_gd,last_five,tcount)

# Do a complex sort, pts, gd 
    s = sorted(table_tup, key=itemgetter(5), reverse=True)
    table_sort = sorted(s, key=itemgetter(4), reverse=True)
    t_team,t_win,t_draw,t_loss,t_pts,t_gd,t_l5,t_tc = zip(*table_sort)


# Print table
    print(" ")
    print("   Team                       W   D   L  Pts  Dif")
    for x in range(0, nteams):
        print("{0:2} {1:25} {2:2d}  {3:2d}  {4:2d}  {5:3d}  {6:+3d} {7}".format(x+1,t_team[x],t_win[x],t_draw[x],t_loss[x],t_pts[x],t_gd[x], t_l5[x]))
        weekly_rank[week][t_tc[x]] = x+1
        weekly_pts[week][t_tc[x]] = t_pts[x]

    print(" ")
#    print(weekly_rank[week])
#    dummy = input(" ")
    
# Update perturbations to team ratings
    for x in range(0, nteams): 
        opert[x] += random.uniform(-pertmag,pertmag)
        dpert[x] += random.uniform(-pertmag,pertmag)
        kpert[x] += random.uniform(-pertmag,pertmag)
#   
#    sys.exit()
    
print(" ")

##### Plot a graph of season's week-by-week team performance
pmax = max(weekly_pts[37])
vtint = 0.05 * (pmax - 25)
plt.xlim((0, 38.5))
plt.ylim((-2, pmax+4))
plt.tick_params(axis='y',left='on',right='on',labelleft='on',labelright='on')
plt.xticks([1, 5, 10, 15, 20, 25, 30, 35, 38])
plt.vlines(19.5,-2,pmax+4,colors="#404040")
for t in range(0, nteams):
    pseries = [x[t] for x in weekly_pts]
    df=pd.DataFrame({'x': range(1,39), 'y': pseries })
    plt.plot('x','y',data=df,color=tcolor2[t],linestyle='-',linewidth=3)
    plt.plot('x','y',data=df,color=tcolor1[t],linestyle='--',linewidth=2)
    plt.text(3.26,pmax-0.04-vtint*(weekly_rank[37][t]-1),abbrs[t],verticalalignment='center',horizontalalignment='right',fontsize=11,color=tcolor2[t],weight='normal')
    plt.text(3.3,pmax-vtint*(weekly_rank[37][t]-1),abbrs[t],verticalalignment='center',horizontalalignment='right',fontsize=11,color=tcolor1[t],weight='normal')
    plt.text(6.96,pmax-0.04-vtint*(weekly_rank[37][t]-1),table_pts[t],verticalalignment='center',horizontalalignment='left',fontsize=11,color=tcolor2[t],weight='normal')
    plt.text(7.0,pmax-vtint*(weekly_rank[37][t]-1),table_pts[t],verticalalignment='center',horizontalalignment='left',fontsize=11,color=tcolor1[t],weight='normal')
    plt.plot([4.00,6.33],[pmax-vtint*(weekly_rank[37][t]-1),pmax-vtint*(weekly_rank[37][t]-1)],color=tcolor2[t],linestyle='-',linewidth=3)
    plt.plot([4.00,6.33],[pmax-vtint*(weekly_rank[37][t]-1),pmax-vtint*(weekly_rank[37][t]-1)],color=tcolor1[t],linestyle='--',linewidth=2)
    
plt.ylabel('Points')
plt.xlabel('Week')
plt.title('Week-by-Week Progression')
# plt.legend()
# plt.figure(figsize=(11,8.5))
plt.show()