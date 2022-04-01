# Imports
import ffmpeg
import os
import subprocess
import re
import pandas as pd
import numpy as np

# adding a function to round values of a list
def round_list_values(the_list, rounding=3):
    return list(np.round(the_list, rounding))

def get_success_array(silence_middle, split_arr):
    i = 0
    success_array = []
    for j, silence_time in enumerate(silence_middle):
        if silence_time < split_arr[i]:
            continue
        else:
            # compare which item is closer to our suggested split time
            prev_silence = silence_middle[j - 1]
            if silence_time - split_arr[i] > split_arr[i] - prev_silence:
                if prev_silence not in success_array:
                    success_array.append(prev_silence)
                else:
                    success_array.append(silence_time)
            else:
                success_array.append(silence_time)
            # move to the next time in the split_arr
            if i < len(split_arr) - 1:
                i += 1
            else:
                break
    return round_list_values(success_array)

def merge_small_durations(diff_arr, min_dur, max_dur, fwd=True):
    dur_arr_mod = []
    flag_raised = False  # the flag will be raised if we merges occur
    for i, dur in enumerate(diff_arr):
        if flag_raised:
            flag_raised = False
            continue
        if (dur < min_dur) & (dur > 0):
            # if dur < min_dur:
            if i + 1 < len(diff_arr):
                next_diff = diff_arr[i + 1]
                if dur + next_diff < max_dur:
                    if fwd: dur_arr_mod.append(0)
                    dur_arr_mod.append(dur + next_diff)
                    if not fwd: dur_arr_mod.append(0)
                    flag_raised = True
            else:
                dur_arr_mod.append(dur)
        else:
            dur_arr_mod.append(dur)
    return round_list_values(dur_arr_mod)

def split_audio_file(
    src,
    result,
    split_interval,
    min_duration,
    max_duration,
):
    split_cmd = f"ffmpeg -i {src} -af silencedetect=n=-20dB:d=0.25 -f null - "
    out = subprocess.Popen(split_cmd,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()
    str_out = str(stdout)
    # FInding all and converting to float in one step
    s_start = map(float, re.findall(r'silence_start: (\d+.\d+)', str_out))
    s_end = map(float, re.findall(r'silence_end: (\d+.\d+)', str_out))
    s_duration = map(float, re.findall(r'silence_duration: (\d+.\d+)',
                                       str_out))

    # zipping all together
    results = list(zip(s_start, s_end, s_duration))
    results_df = pd.DataFrame(
        results, columns=['silence_start', 'silence_end', 'silence_duration'])
    results_df[
        'silence_mid'] = results_df.silence_start + results_df.silence_duration / 2
    end_time = float(ffmpeg.probe(src)['format']['duration'])
    split_arr = np.arange(split_interval, int(end_time), split_interval)
    silence_mid = results_df.silence_mid.to_numpy()
    success_array = get_success_array(silence_mid, split_arr)
    dur_array = [0] + success_array + [end_time]
    difference_array = round_list_values(np.diff(np.array(dur_array)))
    fwd_arr = merge_small_durations(difference_array, min_duration,
                                    max_duration)
    bwd_arr = merge_small_durations(fwd_arr[::-1],
                                    min_duration,
                                    max_duration,
                                    fwd=False)[::-1]
    # stage 1
    final_stops = [x for i, x in enumerate(dur_array[1:]) if bwd_arr[i] != 0]
    # stage 2
    final_stops = final_stops[:-1]
    final_durations = round_list_values(
        np.diff(np.array([0] + final_stops + [end_time])))
    out_times = ",".join(str(e) for e in final_stops)
    slice_cmd = f"ffmpeg -i {src} -vn -c copy -f segment -segment_times "
    slice_cmd += f"{out_times} {result}"
    execute = os.system(slice_cmd)
    if execute == 0:
        print(f"The {src} file was split successfuly")
    else:
        print(f"Error during split of {src} file")
    pass

def find_folder_name(file_number):
    folder_number = (file_number-1) // 7 + 1
    return f"Group_{folder_number:02d}"

def get_output_folder(source_output, file_number):
    folder_name = find_folder_name(file_number)
    folder_path = os.path.join(source_output, folder_name)
    exists = os.path.exists(folder_path)
    if not exists:
        os.makedirs(folder_path)
    return folder_path

## Test

split_interval, min_duration, max_duration = 180, 30, 240
source_folder = "X:/Music/RightlyGuidedCalifate"
output_folder = os.path.join(source_folder, "output2")
test = 10
for file_number in range(test, test+1): #From 5 to 112
    src = os.path.join(source_folder, f"RGC{file_number:03d}_.mp3")
    result = os.path.join(get_output_folder(output_folder, file_number),
                          f"RGC{file_number:03d}_%d.mp3")
    print(file_number, end=". ")
    split_audio_file(src, result, split_interval, min_duration, max_duration)