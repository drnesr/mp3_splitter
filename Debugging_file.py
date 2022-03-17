import numpy as np

split_interval = 60
end_time = 440.502857
success_array = [53.2015355,
 115.09360299999999,
 174.648544,
 247.038247,
 354.971383,
 381.905991,
 421.5824465]
dur_array= [0] + success_array+[end_time]
difference_array = np.diff(np.array(dur_array))

min_duration = 0.8 * split_interval
max_duration = 2.5 * split_interval



# Check each element for the forward round
def merge_small_durations(diff_arr, min_dur, max_dur, fwd=True):
    dur_arr_mod = []
    flag_raised=False # the flag will be raised if we merges occur
    for i, dur in enumerate(diff_arr):
        if flag_raised:
            flag_raised=False
            continue
        if (dur < min_dur) & (dur > 0):
        # if dur < min_dur:
                if i + 1 < len(diff_arr):
                    next_diff = diff_arr[i + 1]
    #                 if next_diff==0:
    #                     next_diff = diff_arr[i + 2]
                    if dur + next_diff < max_dur:
                        if fwd: dur_arr_mod.append(0)
                        dur_arr_mod.append(dur + next_diff)
                        if not fwd: dur_arr_mod.append(0)
                        flag_raised=True
                else:
                    dur_arr_mod.append(dur)
        else:
            dur_arr_mod.append(dur)
    return dur_arr_mod


fwd_arr = merge_small_durations(difference_array, min_duration, max_duration)

bwd_arr = merge_small_durations(fwd_arr[::-1], min_duration,
                                max_duration, fwd=False)[::-1]


# getting the modified success_array
print(success_array)
print(difference_array)
print(fwd_arr)
print(bwd_arr)