#!/usr/bin/env python3
# This tool "eclipse_make_restart.py" is licensed under the MIT License.
# Copyright (c) 2024  Oliver Stueker
#
# Please see the file LICENSE.txt for the full text of the license.
# The license does not extend to any other products or tools,
# unless explicitly stated by their respective authors or copyright holders.
import argparse
from glob import glob
import logging
import os
import re
import shutil
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(sys.argv[0].rstrip('.py'))


def determine_restart_id(basename):
    "Looks for existing $BASENAME.Xiiii and $BASENAME.Siiii files to determine number for restart."

    # 1) find restart-files and determine largest number of *.X[0-9]{4}
    # find all files that are named $BASENAME.Xiiii and sort:
    xfiles = glob('{basename:s}.X[0-9][0-9][0-9][0-9]'.format(basename=basename))
    xfiles.sort()

    if len(xfiles) == 0:
        msg = 'FATAL ERROR:\n'
        msg += 'Did not find any restart file: "{basename:s}.X0000"\n'.format(basename=basename)
        msg += 'exiting.'
        logger.error(msg)
        sys.exit(1)

    # get last four digits
    x_filename = xfiles[-1]
    id = re.search(r'\.X([0-9]{4})$', x_filename).group(1)
    logger.debug('Largest Xiiii file is: {:s}'.format(x_filename))

    # check if corresponding Siii file exists
    s_filename = '{basename:s}.S{id:s}'.format(basename=basename, id=id)
    if not os.path.exists(s_filename):
        msg = 'FATAL ERROR:\n'
        msg += 'Found {x_fn:s},\n'.format(x_fn=x_filename)
        msg += 'but   {s_fn:s} does not exist!\n'.format(s_fn=s_filename)
        msg += 'exiting.'
        logger.error(msg)
        sys.exit(1)

    logger.debug('Found corresponding Siiii file: {:s}'.format(s_filename))
    logger.debug('Next restart number is: {:s}'.format(id))

    return id


def update_data_file(basename, id, **kwargs):
    "Update DATA file for the next restart."
    new_data = []
    data_filename = '{basename:s}.DATA'.format(basename=basename)

    with open(data_filename) as data_file:
        # reset some flags, so we can store where in the file we are
        in_solution = False
        in_schedule = False
        restart_updated = False
        found_restart = False
        found_skiprest = False
        found_include = False
        found_commented_include = False

        # loop over file, line-by-line
        for line in data_file:
            # check for keywords and set flags accordingly
            if line.startswith('SOLUTION'):
                in_solution = True
                # reset some flags for this section
                restart_updated = False
                found_restart = False
                found_include = False
                found_commented_include = False
            elif line.startswith('SUMMARY'):
                # so that we don't comment out anything in SUMMARY
                in_solution = False
            elif line.startswith('SCHEDULE'):
                in_schedule = True
                # reset some flags for this section
                in_solution = False
                found_skiprest = False
                found_include = False
                found_commented_include = False
            elif line.startswith('RESTART'):
                found_restart = True
            elif line.startswith('INCLUDE'):
                found_include = True
            elif re.search(r'^-- *INCLUDE', line):
                found_commented_include = True

            # 2) Add RESTART lines between SOLUTION and INCLUDE, if not already there
            if (in_solution and (found_include or found_commented_include) and not found_restart):
                logger.debug("Adding new RESTART keyword.")
                # restart not yet present
                new_data.append('RESTART\n')
                new_data.append(' {basename:s} {id:s} /\n'.format(basename=basename, id=id))
                new_data.append('\n')
                found_restart = True
                restart_updated = True
                # logger.debug("current line is: {:s}".format(line.strip()))
                logger.info('New RESTART keyword added (report number {:}).'.format(id))

            # 3) If RESTART already there: just update number
            if (found_restart and not restart_updated):
                logger.debug("Updating existing RESTART clause.")
                new_data.append(line)        # append RESTART line
                line = data_file.readline()  # read next line
                line = ' {basename:s} {id:s} /\n'.format(basename=basename, id=id)
                restart_updated = True
                logger.info('Updated RESTART (report number {:})'.format(id))

            # 4) comment out INCLUDE in solution (if not already done)
            if (in_solution and found_include and not found_commented_include):
                logger.debug("Commenting INCLUDE in SOLUTION section.")
                # logger.debug("current line is: {:s}".format(line.strip()))
                # comment line that starts with INCLUDE
                line = '--' + line
                new_data.append(line)
                # also comment next line
                line = '--' + data_file.readline()
                found_commented_include = True

            # 5) Add SKIPREST to SCHEDULE section if not already there
            if (in_schedule and found_include and not found_skiprest):
                logger.debug("Adding SKIPREST to SCHEDULE section.")
                new_data.append('SKIPREST\n\n')
                found_skiprest = True

            new_data.append(line)
    return new_data


if __name__ == "__main__":
    # parse command-line arguments
    parser = argparse.ArgumentParser(
        prog=sys.argv[0],
        description='Updates an Eclipse DATA file for the next restart.',
        # epilog='Text at the bottom of help'
    )
    parser.add_argument('basename', nargs=1,
                        metavar='NAME[.DATA]',
                        help='Name of the DATA file\n(needs to be the same for NAME.X0000 and NAME.S0000 files).',
                        action='store')
    parser.add_argument('-b', '--backup',
                        help='Backup DATA file as "NAME.DATA.BACKUP".',
                        action='store_true')
    parser.add_argument('--restore',
                        help='Restore DATA file from "NAME.DATA.BACKUP" before processing.',
                        action='store_true')
    parser.add_argument('-v', '--verbose',
                        help='Show additional messages for debugging.',
                        action='store_true')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # remove .DATA suffix from basename, if present
    if args.basename[0].endswith('.DATA'):
        basename = args.basename[0].rstrip(".DATA")
    else:
        basename = args.basename[0]

    data_filename = '{basename:s}.DATA'.format(basename=basename)

    # restore DATA file from backup if --restore was used:
    if args.restore:
        backup_filename = '{:s}.BACKUP'.format(data_filename)
        shutil.copyfile(backup_filename, data_filename)
        logger.info('Restored "{:s}" to "{:s}"'.format(backup_filename, data_filename))

    id = determine_restart_id(basename)

    new_data = update_data_file(basename, id)

    # create backup-file, if requested
    if args.backup:
        backup_filename = '{:s}.BACKUP'.format(data_filename)
        shutil.move(data_filename, backup_filename)
        logger.info('Backup created: {:s}'.format(backup_filename))

    # write new data to file
    with open(data_filename, 'w') as data_file:
        data_file.writelines(new_data)
        logger.info('Data file written: {:s}'.format(data_filename))
