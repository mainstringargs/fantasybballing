import sportsline_scraper
import rotowire_scraper
import pandas
import draft_kings
import sys
from datetime import datetime
from dateutil import tz
import rotowire_scraper
from pydfs_lineup_optimizer import get_optimizer, Site, Sport

import traceback
import sys
import csv
import os, glob

print("Args:", str(sys.argv))

contests = draft_kings.Client().contests(sport=draft_kings.Sport.NBA)


def section_of_day(x):
    if (x > 3) and (x < 11):
        return 'Morning'
    elif (x >= 11) and (x < 13):
        return 'Noon'
    elif (x >= 13) and (x <= 17):
        return 'Late'
    else:
        return 'Night'


def gen_pydfs(in_filename, out_filename):
    optimizer = get_optimizer(Site.DRAFTKINGS_CAPTAIN_MODE, Sport.BASKETBALL)

    optimizer.load_players_from_csv(in_filename)

    #optimizer.set_max_repeating_players(1)

    # if you want to see lineups on screen
    for lineup in optimizer.optimize(5):
        print(lineup)
    optimizer.export(out_filename)


sportsline_nba_projections = sportsline_scraper.get_projections();
rotowire_nba_projections = rotowire_scraper.get_projections();

newpath = 'results'
if not os.path.exists(newpath):
    os.makedirs(newpath)

newpath = 'scratch'
if not os.path.exists(newpath):
    os.makedirs(newpath)

now = datetime.now().strftime("%Y%m%d-%H%M%S")


def gen_dfs(nba_projections):
    global newpath, now
    starting_time = contest.starts_at
    to_zone = tz.tzlocal()
    central = starting_time.astimezone(to_zone)
    weekday = central.strftime('%A')
    section = section_of_day(central.hour)
    #   if 'in-game' in contest.name.lower() and contest.entries_details.maximum > 500 and contest.entries_details.fee==.25 and weekday.lower() in sys.argv[1].strip().lower() and section.lower() in sys.argv[2].strip().lower():
    if 'showdown' in contest.name.lower() and contest.entries_details.fee < 1 and 'top 20' not in contest.name.lower() and 'top 15' not in contest.name.lower() and 'top 10' not in contest.name.lower() and 'satellite' not in contest.name.lower() and 'winner takes all' not in contest.name.lower() and weekday.lower() in \
            sys.argv[1].strip().lower() and section.lower() in sys.argv[2].strip().lower():
        print(central)
        print(contest)
        print(weekday, section)
        DK_CONTEST_URL = "https://www.draftkings.com/lineup/getavailableplayerscsv?contestTypeId=96&draftGroupId=" + str(
            contest.draft_group_id)

        teams = contest.name[contest.name.find("(") + 1:contest.name.find(")")].replace(' ', '_')

        LOGDATE = central.strftime("%Y%m%d-%H%M%S")

        dk_df = pandas.read_csv(DK_CONTEST_URL)
        dk_df['Name'] = dk_df.Name.str.replace('Jr.', '').replace('Sr.', '').replace(' III', '').replace('Fuller V',
                                                                                                         'Fuller').str.strip()
        dk_df.to_csv(
            "scratch/roster_" + teams + "_" + LOGDATE + "_" + now + "_" + str(contest.entries_details.maximum) + ".csv",
            index=False);
        merged_dk_df = dk_df.merge(nba_projections, on='Name', how='left')
        merged_dk_df = merged_dk_df[merged_dk_df['Projection'].notna()]
        merged_dk_df = merged_dk_df[merged_dk_df['Projection'] > 0.0]
        merged_dk_df = merged_dk_df.drop('Position_y', axis=1)
        merged_dk_df = merged_dk_df.drop('Team', axis=1)
        merged_dk_df = merged_dk_df.drop('AvgPointsPerGame', axis=1)
        merged_dk_df = merged_dk_df.rename(columns={"Position_x": "Position", "Projection": "AvgPointsPerGame"})
        dk_df_merged_file = "scratch/merged_" + teams + "_" + LOGDATE + "_" + now + "_" + str(
            contest.entries_details.maximum) + ".csv";
        merged_dk_df.to_csv(dk_df_merged_file, index=False);

        newpath = 'temp'

        if os.path.exists(newpath):
            for file in os.scandir(newpath):
                os.remove(file.path)

        if not os.path.exists(newpath):
            os.makedirs(newpath)

        gen_pydfs(dk_df_merged_file, newpath + '/pydfs_result.csv')

        extension = 'csv'
        all_filenames = [i for i in glob.glob('temp/*.{}'.format(extension))]

        combined_csv = pandas.concat([pandas.read_csv(f) for f in all_filenames])

        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        combined_csv = combined_csv.fillna('pydfs')
        combined_csv = combined_csv.sort_values('FPPG', ascending=False)
        # export to csv
        combined_csv.to_csv("results/nba_combined_results_" + teams + "_" + LOGDATE + "_" + now + "_" + str(
            contest.entries_details.maximum) + ".csv", index=False, encoding='utf-8-sig',
                            header=['CPT', 'UTIL', 'UTIL', 'UTIL', 'UTIL', 'UTIL', 'Budget', 'FPPG'])


for contest in contests.contests:
    try:
        gen_dfs(rotowire_nba_projections)
    except Exception:
        print(traceback.format_exc())
        try:
            gen_dfs(sportsline_nba_projections)
        except Exception:
            print(traceback.format_exc())