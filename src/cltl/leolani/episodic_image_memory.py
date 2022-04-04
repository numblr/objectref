# general imports for EMISSOR and the BRAIN
from cltl import brain
from emissor.representation.scenario import ImageSignal

# specific imports
from datetime import datetime
import time
import cv2
import pathlib
import emissor_api
import face_util
import capsule_util


def get_next_image(camera, imagefolder):
    what_is_seen = None

    success, frame = camera.read()
    if success:
        current_time = int(time.time() * 1e3)
        imagepath = f"{imagefolder}/{current_time}.png"
        image_bbox = (0, 0, frame.shape[1], frame.shape[0])
        cv2.imwrite(imagepath, frame)
        print(imagepath)

        what_is_seen = face_util.detect_objects(imagepath)

    return what_is_seen, current_time, image_bbox


def create_imageSignal_and_annotations_in_emissor (results, image_time, image_bbox, scenario_ctrl):

    #### We create an imageSignal
    imageSignal = emissor_api.create_image_signal(scenario_ctrl, f"{image_time}.png", image_bbox, image_time)
    scenario_ctrl.append_signal(imageSignal)
    what_is_seen = []
    ## The next for loop creates a capsule for each object detected in the image and posts a perceivedIn property for the object in the signal
    ## The "front_camera" is the source of the signal
    for result in results:
        current_time = int(time.time() * 1e3)

        bbox = [int(num) for num in result['yolo_bbox']]
        object_type = result['label_string']
        object_prob = result['det_score']
        what_is_seen.append(object_type)
        mention = face_util.create_object_mention(imageSignal, "front_camera", current_time, bbox, object_type,
                                               object_prob)
        imageSignal.mentions.append(mention)

    return what_is_seen, imageSignal

def add_perception_to_episodic_memory (imageSignal: ImageSignal, object_list, my_brain,  scenario_ctrl, location, place_id):
    response_list = []
    for object in object_list:
        ### We created a perceivedBy triple for this experience,
        ### @TODO we need to include the bouding box somehow in the object
        #print(object)
        capsule = capsule_util.scenario_image_triple_to_capsule(scenario_ctrl,
                                                          imageSignal,
                                                          location,
                                                          place_id,
                                                          "front_camera",
                                                          object,
                                                          "perceivedIn",
                                                          imageSignal.id)
        
        #print(capsule)
        # Create the response from the system and store this as a new signal
        # We use the throughts to respond
        response = my_brain.update(capsule, reason_types=True, create_label=True)
        response_list.append(response)
    return response_list


def watch_and_remember(scenario_ctrl,
                       camera,
                       imagefolder,
                       my_brain,
                       location,
                       place_id):

    t1 = datetime.now()
    while (datetime.now()-t1).seconds <= 60:
        ###### Getting the next input signals
        what_did_i_see, current_time, image_bbox = get_next_image(camera, imagefolder)
        object_list, imageSignal = create_imageSignal_and_annotations_in_emissor(what_did_i_see, current_time, image_bbox, scenario_ctrl)
        response = add_perception_to_episodic_memory(imageSignal, object_list, my_brain, scenario_ctrl, location, place_id)
        print(response)
        reply = "\nI saw: "
        if len(object_list) > 1:
            for index, object in enumerate(object_list):
                if index == len(object_list) - 1:
                    reply += " and"
                reply += " a " + object
        elif len(object_list) == 1:
            reply += " a " + object_list[0]
        else:
            reply = "\nI cannot see! Something wrong with my camera."

        print(reply + "\n")





def main():
    ### Link your camera
    camera = cv2.VideoCapture(0)
    # Initialise the brain in GraphDB

   ##### Setting the agents
    AGENT = "Leolani2"
    HUMAN_NAME = "Stranger"
    HUMAN_ID = "stranger"
    scenarioStorage, scenario_ctrl, imagefolder, rdffolder, location, place_id = emissor_api.start_a_scenario(AGENT, HUMAN_ID, HUMAN_NAME)

    log_path = pathlib.Path(rdffolder)
    my_brain = brain.LongTermMemory(address="http://localhost:7200/repositories/sandbox",
                                    log_dir=log_path,
                                    clear_all=True)

    watch_and_remember(scenario_ctrl, camera, imagefolder, my_brain, location, place_id)
    scenario_ctrl.scenario.ruler.end = int(time.time() * 1e3)
    scenarioStorage.save_scenario(scenario_ctrl)
    camera.release()

if __name__ == '__main__':
    main()
    

