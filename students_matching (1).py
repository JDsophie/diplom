import random
import pandas as pd
import numpy as np

from collections import Counter

class StudentsMatching:
    def __init__(self, num_students, num_profiles, perc_of_target,
                 perc_of_contract, debts_limit, first_pref, first_pref_target,
                 min_num_groups, max_num_groups, min_group_sizes, max_group_sizes):
        self.num_students = num_students
        self.num_profiles = num_profiles
        self.perc_of_target = perc_of_target
        self.perc_of_contract = perc_of_contract
        self.debts_limit = debts_limit
        self.first_pref = first_pref
        self.first_pref_target = first_pref_target
        self.min_num_groups = min_num_groups
        self.max_num_groups = max_num_groups
        self.min_group_sizes = min_group_sizes
        self.max_group_sizes = max_group_sizes
        
        self.data_s = pd.DataFrame(index=list(range(self.num_students)))
        self.data_p = pd.DataFrame(index=list(range(self.num_profiles)))
        
        self.priorities = None
        self.priorities_target = None
        self.reserve_size = None
        self.sorted_students = None
        self.unmatched_students = None
        
        self.profiles_matches = {prof: [] for prof in range(self.num_profiles)}
        self.student_matches = {student: None for student in range(self.num_students)}

        self.generate_student_labels()
        self.generate_debts()
        self.generate_rating()
        self.generate_profiles()
        self.generate_student_preferences()
        self.generate_profile_preferences()
        
        self.mandatory_profiles = self.calculate_mandatory_profiles()
        self.reserve_students = self.fill_reserve()

    def generate_student_labels(self):
        num_target_students = int(self.perc_of_target * self.num_students)
        self.data_s['target'] = 0
        rand_ind = np.random.choice(self.data_s.index, size=num_target_students, replace=False)
        self.data_s.loc[rand_ind, 'target'] = 1
        
        num_contract_students = int(self.perc_of_contract * self.num_students)
        self.data_s['contract'] = 0
        rand_ind = np.random.choice(self.data_s.index, size=num_contract_students, replace=False)
        self.data_s.loc[rand_ind, 'contract'] = 1

    def generate_debts(self):
        def generate_single_debt():
            return random.choices(range(8), weights=[10, 5, 3, 3, 2, 2, 1, 1], k=1)[0]

        self.data_s['debts'] = [generate_single_debt() for _ in self.data_s.index]

    def generate_rating(self):
        self.data_s['rating'] = [random.randint(0, 500) for _ in self.data_s.index]
    
    def generate_profiles(self):
        self.data_p['min_num_groups'] = self.min_num_groups
        self.data_p['max_num_groups'] = self.max_num_groups
        self.data_p['min_group_size'] = self.min_group_sizes
        self.data_p['max_group_size'] = self.max_group_sizes
        self.data_p['quota'] = self.data_p['max_group_size'] * self.data_p['max_num_groups']
        
    def generate_student_preferences(self):
        preferences_s = {}
        for student in self.data_s.index:
            if (self.data_s['debts'][student] > self.debts_limit) & (self.data_s['target'][student] == 0):
                preferences_s[student] = []
            else:
                preferences_s[student] = random.sample(list(self.data_p.index), k=self.num_profiles)
        self.data_s['preferences'] = self.data_s.index.map(preferences_s)
        
    def generate_profile_preferences(self):
        self.sorted_students = self.data_s.sort_values(by=['target', 'debts', 'rating', 'contract'], ascending=[False, True, False, False]).index.tolist()
        self.data_p['preferences'] = [self.sorted_students] * len(self.data_p)
    
    def calculate_mandatory_profiles(self):
        self.priorities = Counter([x[0] for x in self.data_s['preferences'] if x])
        self.priorities_target = Counter([x[0] for x in self.data_s[self.data_s['target'] == 1]['preferences'] if x])
        mandatory_profiles = list(set(
            [profile for profile, count in self.priorities.items() if count > self.first_pref] +
            [profile for profile, count in self.priorities_target.items() if count > self.first_pref_target]
        ))
        self.data_p.loc[(self.data_p.index.isin(mandatory_profiles)) & (self.data_p['min_num_groups'] == 0), 'min_num_groups'] = 1
        num_mandatory_profiles = len(mandatory_profiles)
        return mandatory_profiles
        
    def calculate_reserve_size(self):
        return (self.data_p['min_group_size'] * self.data_p['min_num_groups']).sum() 
    
    def fill_reserve(self):
        self.reserve_size = self.calculate_reserve_size()
        poor_students = self.data_s[self.data_s['preferences'].apply(lambda x: not x)].shape[0]
        if poor_students > self.reserve_size:
            reserve_students = self.sorted_students[-poor_students:]
        else:
            reserve_students = self.sorted_students[-self.reserve_size:]
        return reserve_students
    
    def gale_shapley(self, data):
        free_students = [s for s in data if s not in self.reserve_students]  
        proposed = {student: 0 for student in range(self.num_students)}
        while free_students:
            student = free_students[0]
            student_pref = self.data_s.loc[student, 'preferences']
            prof_index = proposed[student]
            if prof_index < len(student_pref):  
                prof = student_pref[prof_index]
                proposed[student] += 1
                if len(self.profiles_matches[prof]) < self.data_p['quota'][prof]:
                    self.profiles_matches[prof].append(student)
                    self.student_matches[student] = prof
                    free_students.pop(0)
                    if prof in self.mandatory_profiles and self.reserve_students:
                        student_from_reserve = self.reserve_students.pop(-1)
                        free_students.append(student_from_reserve)
                else:
                    current_student = self.profiles_matches[prof][-1]
                    prof_pref = self.data_p['preferences'][prof]
                    if prof_pref.index(student) < prof_pref.index(current_student):
                        self.profiles_matches[prof].pop()
                        self.profiles_matches[prof].append(student)
                        self.profiles_matches[prof].sort(key=prof_pref.index)
                        self.student_matches[student] = prof
                        self.student_matches[current_student] = None
                        free_students.pop(0)
                        free_students.append(current_student)
            else:
                free_students.pop(0)
        self.unmatched_students = [s for s in range(self.num_students) if self.student_matches[s] is None]
           
    def gale_shapley_short(self):
        free_students = [s for s in self.sorted_students if s not in self.reserve_students]
        proposed = {student: 0 for student in range(self.num_students)}
        while free_students:
            student = free_students[0]
            student_pref = self.data_s.loc[student, 'preferences']
            prof_index = proposed[student]
            if prof_index < len(student_pref):  
                prof = student_pref[prof_index]
                proposed[student] += 1
                if len(self.profiles_matches[prof]) < self.data_p['quota'][prof]:
                    self.profiles_matches[prof].append(student)
                    self.student_matches[student] = prof
                    free_students.pop(0)
                    if prof in self.mandatory_profiles and self.reserve_students:
                        student_from_reserve = self.reserve_students.pop(-1)
                        free_students.append(student_from_reserve)
            else:
                free_students.pop(0)
        self.unmatched_students = [s for s in range(self.num_students) if self.student_matches[s] is None]