#  Add missing file classifications
#   amf
#   Feb 2022, updated Dec 2025
#
#   Uses Flywheel's dataview tool to:
#       (1) get all files in a project
#       (2) select only nifti's w/o file.classification fields
#       (3) Look for files in same acquisition with existing classifications & uses to update this file
#       (4) If no existing classifications found, runs the file-classifier gear on the file
#

import flywheel
import os
# import backoff
# from flywheel.rest import ApiException

fw_api_token = os.getenv("FW_API_KEY")
# export FLYWHEEL_SDK_REQUEST_TIMEOUT=600

# ====== access the flywheel client for the instance ====== 
fw = flywheel.Client(fw_api_token)

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
print(f'STARTUP Initialized DataView')

# ====== initialize gear ==========
gear2run = fw.lookup('gears/file-classifier')
print(f'STARTUP Loaded gear to run')

# ====== loop through projects ======
for project in fw.projects.iter(limit=5):
    proj_label = project.label
    if "_v2" in proj_label:
        print('PROCESSING: '+proj_label)
        project = fw.projects.find_first('label='+proj_label)
        project = project.reload()
        # get a dataframe with all files in this proj
        df = fw.read_view_dataframe(view, project.id)
        if not df.empty:
            # print(df)
            # get the classification profile
            for project_file in project.files:
                if project_file.name == 'MR_combined.yaml':
                    project_class_profile = project_file
                    print('USING PROFILE: '+project_file.name)
            # df = df[df['file.modality']=='MR'] # filter to files with no metadata
            df_sub = df[(df['file.classification.Intent'].isnull()) & \
                        (df['file.classification.Features'].isnull()) & \
                        (df['file.classification.Measurement'].isnull())]
            # filter to only nifti files
            df_sub = df_sub[df_sub['file.type']=='nifti']
            # loop through the nifti files missing classification
            for index, row in df_sub.iterrows():
                file_id = row['file.id']
                file_name = row['file.name']
                acq_id = row['acquisition.id']
                acq_rows = df[df['acquisition.id']==acq_id]
                acq_rows = acq_rows[acq_rows['file.id']!=file_id]
                modalities = acq_rows['file.modality'].drop_duplicates().tolist()
                acq = fw.get_acquisition(acq_id)
                if '' in modalities:
                    modalities.remove('')
                ## look for any existing classifications in the same acquisition,
                #   if exist then use to update the missing file classification
                if (not acq_rows[~acq_rows['file.classification.Intent'].isnull()].empty) | \
                    (not acq_rows[~acq_rows['file.classification.Features'].isnull()].empty) | \
                    (not acq_rows[~acq_rows['file.classification.Measurement'].isnull()].empty): # if it's not empty
                    print('UPDATING: '+('/'.join([row['subject.label'],row['session.label'],row['acquisition.label'],row['file.name']])))
                    first_row = acq_rows.iloc[0] # grab the first file in the acqusition
                    classification_in = {}
                    if first_row['file.classification.Intent']:
                        classification_in['Intent'] = first_row['file.classification.Intent']
                    if first_row['file.classification.Features']:
                        classification_in['Features'] = first_row['file.classification.Features']
                    if first_row['file.classification.Measurement']:
                        classification_in['Measurement'] = first_row['file.classification.Measurement']
                    try:
                        acq.replace_file_classification(file_name, \
                                                        classification=classification_in, \
                                                        modality=modalities[0] )
                    except:
                        continue
                else:
                    ## run the file classifier gear
                    for file_ in acq.files:
                        if file_.type == 'nifti':
                            inputs = {'file-input':[],
                                    'profile':[]}
                            inputs['file-input'] = file_
                            inputs['profile'] = project_class_profile
                            gear2run.run(inputs=inputs)
                            print('QUEUED: '+('/'.join([row['subject.label'],row['session.label'],row['acquisition.label'],row['file.name']])))
