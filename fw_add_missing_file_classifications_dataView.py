#  Add missing file classifications
#   amf
#   Feb 2022
#
#   Uses Flywheel's dataview tool to get all files in a project & select only nifti's w/o file.classification fields
#   Looks for files in same acquisition with existing classifications & uses to update this file
#

import flywheel
import os
# import backoff
# from flywheel.rest import ApiException

fw_api_token = os.getenv("FLYWHEEL_API_TOKEN")

# ====== access the flywheel client for the instance ====== 
fw = flywheel.Client(fw_api_token) # d3b dev


# ====== set up data view ==========
view = fw.View(
    container="acquisition",
    filename="*",
    match="all",
    columns=[
        "file.name",
        "file.id",
        "file.modality",
        "file.classification.Intent",
        "file.classification.Features",
        "file.classification.Measurement",
        "file.type"
    ],
    include_ids=True,
    include_labels=True,
    process_files=False,
    sort=False,
)

# ====== loop through projects ======
for project in fw.projects.iter():
    proj_label = project.label
    project = fw.projects.find_first('label='+proj_label);
    print('PROCESSING: '+proj_label)
    df = fw.read_view_dataframe(view, project.id) # dataframe with all files in this proj
    df = df[df['file.modality']=='MR'] # filter to nifti's with no metadata
    df_sub = df[(df['file.classification.Intent'].isnull()) & \
                (df['file.classification.Features'].isnull()) & \
                (df['file.classification.Measurement'].isnull())]
    df_sub = df_sub[df_sub['file.type']=='nifti']
    for index, row in df_sub.iterrows(): # loop through the nifti files
        file_id = row['file.id']
        file_name = row['file.name']
        acq_id = row['acquisition.id']
        acq_rows = df[df['acquisition.id']==acq_id]
        acq_rows = acq_rows[acq_rows['file.id']!=file_id]
        ## look for any existing classifications, if exist then use to update the missing file classification
        if (not acq_rows[~acq_rows['file.classification.Intent'].isnull()].empty) & \
            (not acq_rows[~acq_rows['file.classification.Features'].isnull()].empty) & \
            (not acq_rows[~acq_rows['file.classification.Measurement'].isnull()].empty): # if it's not empty
            first_row = acq_rows.iloc[0] # grab the first file in the acqusition
            class_intent = first_row['file.classification.Intent']
            class_features = first_row['file.classification.Features']
            class_measurement = first_row['file.classification.Measurement']
            acq = fw.get_acquisition(acq_id)
            acq.replace_file_classification(file_name, \
                                            classification={
                                                'Intent': class_intent,
                                                'Features': class_features,
                                                'Measurement': class_measurement } )
            print('UPDATED: '+('/'.join([row['subject.label'],row['session.label'],row['acquisition.label'],row['file.name']]))+' to ['+(' '.join(class_intent))+']['+(' '.join(class_features))+']['+(' '.join(class_measurement))+']')

