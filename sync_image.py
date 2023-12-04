import datetime
import subprocess

parent_folder_path = '/www-data/mangamonster.com/storage/app/public/images/manga/'

# Get the current date in yyyy/mm/dd format
today = datetime.datetime.now()
today_str = '{}/{}/{}'.format(str(today.year), str(today.month), str(today.day))

# Define the source and destination folders
processing_folder = f'{parent_folder_path}{today_str}/'
# destination_folder = f'{parent_folder_path}{current_date}'

# Construct the rsync command
rsync_command = f'scp -P 3875  -r {processing_folder}/* bidgear@snapshot-99629717-centos-16gb-hil-1:{processing_folder}'

# Run the rsync command
try:
    subprocess.run(rsync_command, shell=True, check=True)
    print('Rsync completed successfully!')
except subprocess.CalledProcessError as e:
    print(f'Error: {e}')
