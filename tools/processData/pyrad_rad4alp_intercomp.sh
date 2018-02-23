#!/bin/bash

# Call the realtime processing application with arguments.
#  $1 : config file
#  $2 : log file
#  $3 : Set to 1, if the log file must be renamed.
#  $4 : Appendix to log file if $3 is true.
function postprocessing {
    if [ $4 != 0 ]; then
        # Rename logfiles (day changed)
        if [ -f $3 ]; then
            mv $3 $3$5
        fi
    fi

    # Run postproc processing
    cd ${pyradpath}
    python -u main_process_data.py $1 -i $2 >>$3 2>>$3
}

# Call the realtime processing application with arguments.
#  $1 : config file
#  $2 : start date of the processing
#  $3 : End date of the processing
#  $4 : log file
#  $5 : Set to 1, if the log file must be renamed.
#  $6 : Appendix to log file if $5 is true.
function dataquality {
    if [ $6 != 0 ]; then
        # Rename logfiles (day changed)
        if [ -f $5 ]; then
            mv $5 $5$7
        fi
    fi
    
    # Run postproc processing
    cd ${pyradpath}
    python -u main_process_data_period.py $1 $2 $3 --starttime '000001' --endtime '240000' -i $4 >>$5 2>>$5
}

# set permits
umask 0002

CURRENT_TIME=$(date --utc)

# activate pyrad environment
source /srn/analysis/anaconda3/bin/activate pyrad

proc_start=`date +%s`

pyradpath="$HOME/pyrad/src/pyrad_proc/scripts/"

# File where to save day of last cron run
POSTPROC_LASTSTATE="$HOME/intercomp_pyrad/intercomp_laststate.txt"

# Check if new day: if yes rename logfiles
RENAME_LOGFILES=0
LOG_APPENDIX=''
TODAY=`date --utc +"%Y%m%d"`
if [ -f $POSTPROC_LASTSTATE ]; then
    LASTSTATE=`cat $POSTPROC_LASTSTATE`
    if [ $TODAY != $LASTSTATE ]; then
        RENAME_LOGFILES=1
        LOG_APPENDIX="_$LASTSTATE"
        echo $TODAY > $POSTPROC_LASTSTATE
    fi
    START_TIME=$LASTSTATE
else
    echo $TODAY > $POSTPROC_LASTSTATE
    START_TIME=$(date --date ${TODAY}'-24 hours' +"%Y%m%d")
fi
END_TIME=$(date --date ${TODAY}'-24 hours' +"%Y%m%d")

# log data
echo "PROCESSING START TIME: "${CURRENT_TIME}
echo "START TIME OF DATA TO BE PROCESSED "${START_TIME}
echo "END TIME OF DATA TO BE PROCESSED "${END_TIME}

# radar average
RADAR_VEC=( A D L P W )
nrad=${#RADAR_VEC[@]}

for ((irad=0; irad<${nrad}; irad++)); do
    RADAR=${RADAR_VEC[${irad}]}
    
    echo "PROCESSING PL${RADAR} average"
    proc_start_int=`date +%s`

    CONFIGFILE=rad4alp_avg_PL${RADAR}.txt
    LOGFILE=$HOME/log/rad4alp_avg_PL${RADAR}.log    
    dataquality $CONFIGFILE  $START_TIME $END_TIME $RADAR $LOGFILE $RENAME_LOGFILES $LOG_APPENDIX

    proc_end_int=`date +%s`
    runtime_int=$((proc_end_int-proc_start_int))
    echo "Run time: ${runtime_int} s"
done
    
# radar intercomp
echo "PROCESSING radar intercomparison"
proc_start_int=`date +%s`

CONFIGFILE=rad4alp_intercomp.txt
LOGFILE=$HOME/log/rad4alp_intercomp.log
dataquality $CONFIGFILE  $START_TIME $END_TIME intercomp $LOGFILE $RENAME_LOGFILES $LOG_APPENDIX

# Copy data to rad4alp archive
ORIG_FILES="/srn/analysis/pyrad_products/rad4alp_intercomp/*_dBZ*_avg_intercomp/*INTERCOMP_TS/*.png"
DEST_PATH="/www/proj/Radar/LIVE/archive/ARCHIVE/mon_pol/"
cp ${ORIG_FILES} ${DEST_PATH}


proc_end_int=`date +%s`
runtime_int=$((proc_end_int-proc_start_int))
echo "Run time: ${runtime_int} s"


source /srn/analysis/anaconda3/bin/deactivate

proc_end=`date +%s`
runtime=$((proc_end-proc_start))

CURRENT_TIME=$(date --utc)
echo "PROCESSING END TIME: "${CURRENT_TIME}
echo "Total run time: ${runtime} s"