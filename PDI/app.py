from flask import Flask, render_template, request,flash
import tensorflow as tf
from keras.models import load_model
from tensorflow.keras.preprocessing import image
from keras.metrics import AUC
import numpy as np
import spacy
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer, ChatterBotCorpusTrainer
from flask import *
import pickle
from flask_mysqldb import *
import os
import cv2
import numpy as np
import base64



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
dependencies = {
    'auc_roc': AUC
}

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'nehal'
app.config['MYSQL_DB'] = 'plant'
mysql = MySQL(app)

def register():
    if request.method == 'POST':
        uname = request.form['uname']
        pwd = request.form['pwd']
        
        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Check if account exists using MySQL)
    cur.execute('SELECT * FROM reg WHERE username = %s', (uname,))
    account = cur.fetchone()
    # If account exists show error and validation checks
    if account:
        msg = "Username already registered"
        flash("Username already registered")
        return render_template('register.html',msg=msg)
    else:
        cur.execute('INSERT INTO reg VALUES (%s, %s)', (uname, pwd))
        mysql.connection.commit()
        msg = "Register success"
        flash("Register success")
        return render_template('register.html',msg=msg)
    

Disease_name = {
 0:":Apple scab disease",
 1:'Black rot disease of apple plant',
 2:'Cedar apple rust disease of apple plant',
 3:'Healthy Apple plant Leaf',
 4:'Healthy Blueberry plant Leaf',
 5:'Powdery mildew disease of cherry plant',
 6:'Healthy cherry plant leaf',
 7:'Cercospora leaf_spot Gray_leaf_spot in Corn(maize) plant',
 8:'Common rust disease of corn(maize) plant',
 9:'Northern Leaf Blight of corn(maize) plant',
 10:'Healthy Corn_(maize) leaf',
 11:'Black_rot disease in grape plant',
 12:'Esca (Black_Measles) in grape plant leaf',
 13:'Leaf blight (Isariopsis_Leaf_Spot) in grape plant leaf',
 14:'Healthy leaf of grape plant',
 15:'Haunglongbing (Citrus_greening) in orange plant',
 16:'Bacterial_spot in Peach plant',
 17:'Healthy peach plant leaf',
 18:'bell Bacterial_spot in pepper plant leaf',
 19:'Healthy Pepper Plant Leaf',
 20:'Early blight disease in Potato Plant',
 21:'Late_blight disease in Potato Plant',
 22:'Healthy image of potato plant',
 23:'Healthy image of Raspberry plant',
 24:'Healthy Soybean plant leaf',
 25:'Powdery mildew of Squash plant',
 26:'Leaf scorch disease in Strawberry plant leaf',
 27:'Healthy Strawberry leaf',
 28:'Bacterial spot in Tomato Leaves',
 29:'Early blight disease in Tomato Leaf',
 30:'Late blight disease in Tomato Leaf',
 31:'Leaf Mold disease in Tomato Leaf',
 32:'Septoria leaf Spot disease in Tomato Leaf',
 33:'Spider mites/Two-spotted spider mite disease in Tomato Leaf',
 34:'Target_Spot disease in Tomato Leaf',
 35:'Yellow Leaf Curl Virus disease in Tomato Leaf',
 36:'mosaic virus disease in Tomato Leaf',
 37:'Healthy Tomato Leaf'}

Content_name={
 0:":Apple scab is a fungal disease that affects apple trees. It is caused by the pathogen Venturia inaequalis. The disease primarily affects the leaves, fruit, and twigs of the apple tree. Infected leaves develop dark, scaly lesions, while infected fruits exhibit dark, corky spots. Apple scab can significantly reduce fruit quality and yield if not properly managed.",
 1:'Black rot is a common fungal disease that affects apple trees. It is caused by the pathogen Botryosphaeria obtusa. The disease causes circular, expanding lesions on the leaves, fruit, and twigs of the apple tree. The lesions often have a black or dark brown color, hence the name "black rot." Infected fruit may shrivel, mummify, and become unmarketable.',
 2:'Cedar apple rust is a fungal disease that affects apple trees, as well as cedar and juniper trees. It is caused by the pathogen Gymnosporangium juniperi-virginianae. The disease typically manifests as orange or rust-colored galls on the apple tree leaves, fruit, and twigs. It can cause defoliation, stunted growth, and reduced fruit quality.',
 3:'The "Apple Healthy" category represents healthy apple leaf without any apparent diseases or disorders. The leaves appear normal, without any signs of infection or damage',
 4:'The "Blueberry Healthy" category represents healthy blueberry plants leaf without any evident diseases or disorders. The leaves appear normal and free from any visible symptoms of infection or damage.',
 5:'Cherry Powdery mildew is a fungal disease that affects cherry trees. It is caused by several species of the order Erysiphales. The disease presents as a powdery white or grayish coating on the leaves, stems, and fruit of the cherry tree. Infected leaves may become distorted, and severely affected fruit can become deformed or cracked.',
 6:'The "Cherry Healthy" category represents healthy cherry leaves without any apparent diseases or disorders. The leaves appear normal and show no signs of infection or damage.',
 7:'Cercospora leaf spot, also known as gray leaf spot, is a common fungal disease that affects corn (maize) plants. It is caused by the pathogen Cercospora zeae-maydis. The disease causes small, grayish-brown lesions with a yellow halo on the leaves of corn plants. Severe infections can lead to defoliation and yield reduction.',
 8:'Common rust is a fungal disease that affects corn (maize) plants. It is caused by the pathogen Puccinia sorghi. The disease causes orange or reddish-brown pustules to form on the leaves, husks, and stalks of corn plants. While it can reduce yields, common rust is typically not a significant threat to corn production.',
 9:'Northern leaf blight is a fungal disease that affects corn (maize) plants. It is caused by the pathogen Exserohilum turcicum. The disease produces long, elliptical lesions with gray-green centers and tan borders on the leaves of corn plants. Severe infections can result in premature leaf death, reduced photosynthesis, and yield losses.',
 10:'The "Corn Healthy" category represents healthy corn (maize) plants without any apparent diseases or disorders. The leaves appear normal and show no signs of infection or damage.',
 11:'Black rot is a fungal disease that affects grapevines. It is caused by the pathogen Guignardia bidwellii. The disease primarily affects the leaves and fruit of grapevines. Infected leaves develop black, circular lesions with a yellow border, while infected fruits exhibit brown, shriveled berries. Black rot can cause significant yield losses if not properly managed.',
 12:'Esca, also known as black measles, is a complex fungal disease that affects grapevines. It is caused by several pathogens, including Phaeomoniella chlamydospora, Phaeoacremonium spp., and others. The disease leads to the development of characteristic foliar symptoms, such as leaf chlorosis, necrosis, and reddish discoloration. Esca can cause severe decline and death of grapevines.',
 13:'Leaf blight, also known as Isariopsis leaf spot, is a fungal disease that affects grapevines. It is caused by the pathogen Isariopsis spp. The disease causes small, brown spots on the leaves, which gradually enlarge and develop a grayish-white center with a dark border. Severe infections can lead to defoliation and reduced grape yield.',
 14:'The "Grape Healthy" category represents healthy grapevines without any apparent diseases or disorders. The leaves appear normal, without any signs of infection or damage.',
 15:'Huanglongbing (HLB), also known as citrus greening disease, is a devastating bacterial disease that affects citrus trees, including oranges. It is caused by the bacterium Candidatus Liberibacter spp. The disease causes leaf mottling, yellowing, and vein corking. Infected fruits are small, lopsided, and bitter. HLB can lead to severe economic losses in the citrus industry.',
 16:'Bacterial spot is a common bacterial disease that affects peach trees. It is caused by the pathogen Xanthomonas arboricola pv. pruni. The disease causes dark, water-soaked lesions on the leaves, fruit, and twigs of peach trees. Infected fruits may develop raised, corky spots. Severe infections can lead to defoliation and reduced fruit quality.',
 17:'The "Peach Healthy" category represents healthy peach leaf without any apparent diseases or disorders. The leaves appear normal and show no signs of infection or damage.',
 18:'Bacterial spot is a common bacterial disease that affects bell peppers and other pepper varieties. It is caused by the pathogen Xanthomonas campestris pv. vesicatoria. The disease causes small, water-soaked lesions on the leaves, fruit, and stems of pepper plants. Infected fruit may develop raised, corky spots. Bacterial spot can lead to significant yield losses if not managed properly.',
 19:'The "Pepper, Bell Healthy" category represents healthy bell pepper plants without any apparent diseases or disorders. The leaves appear normal and show no signs of infection or damage.',
 20:'Early blight is a fungal disease that affects potato plants. It is caused by the pathogen Alternaria solani. The disease causes dark, concentric lesions with a target-like appearance on the leaves, stems, and tubers of potato plants. Infected plants may experience defoliation and reduced yield. Early blight is a common concern in potato cultivation.',
 21:'Late blight is a devastating fungal disease that affects potato plants. It is caused by the pathogen Phytophthora infestans. The disease causes dark, water-soaked lesions on the leaves, stems, and tubers of potato plants. Infected tissues may turn brown and become soft. Late blight can rapidly spread and result in significant yield losses if not controlled.',
 22:'The "Potato Healthy" category represents healthy potato plants without any apparent diseases or disorders. The leaves appear normal, without any signs of infection or damage.',
 23:'The "Raspberry Healthy" category represents healthy raspberry plants without any evident diseases or disorders. The leaves appear normal and free from any visible symptoms of infection or damage.',
 24:'The "Soybean Healthy" category represents healthy soybean plants without any apparent diseases or disorders. The leaves appear normal and show no signs of infection or damage.',
 25:'Powdery mildew is a fungal disease that affects squash plants. It is caused by several species of the order Erysiphales. The disease presents as a white, powdery coating on the leaves, stems, and fruit of squash plants. Infected leaves may become distorted, and severely affected fruit can be stunted or malformed.',
 26:'Leaf scorch is a fungal disease that affects strawberry plants. It is caused by the pathogen Diplocarpon earlianum. The disease causes dark, irregular lesions with a reddish margin on the leaves of strawberry plants. Severe infections can result in defoliation and reduced fruit production.',
 27:'The "Strawberry Healthy" category represents healthy strawberry plants without any apparent diseases or disorders. The leaves, stems, and fruits appear normal and show no signs of infection or damage.',
 28:'Bacterial spot is a common bacterial disease that affects tomato plants. It is caused by the pathogen Xanthomonas campestris pv. vesicatoria. The disease causes small, water-soaked lesions on the leaves, stems, and fruit of tomato plants. Infected fruit may develop raised, corky spots. Bacterial spot can lead to significant yield losses if not managed properly.',
 29:'Early blight is a fungal disease that affects tomato plants. It is caused by the pathogen Alternaria solani. The disease causes dark, concentric lesions with a target-like appearance on the leaves, stems, and fruit of tomato plants. Infected plants may experience defoliation and reduced yield. Early blight is a common concern in tomato cultivation',
 30:'Late blight is a destructive fungal disease that affects tomato plants. It is caused by the pathogen Phytophthora infestans. The disease causes dark, water-soaked lesions on the leaves, stems, and fruit of tomato plants. Infected tissues may turn brown and become mushy. Late blight can spread rapidly and lead to significant yield losses.',
 31:'Leaf mold is a fungal disease that affects tomato plants. It is caused by the pathogen Passalora fulva (formerly known as Fulvia fulva or Cladosporium fulvum). The disease primarily affects the leaves of tomato plants, causing yellowing, browning, and the development of fuzzy gray or brown mold on the lower leaf surface. Leaf mold can reduce plant vigor and fruit quality.',
 32:'Septoria leaf spot is a fungal disease that affects tomato plants. It is caused by the pathogen Septoria lycopersici. The disease causes small, dark brown spots with a light center on the leaves of tomato plants. As the infection progresses, the spots may merge and lead to defoliation. Septoria leaf spot can impact yield and fruit quality.',
 33:'Spider mites, specifically the two-spotted spider mite (Tetranychus urticae), are common pests that affect tomato plants. These tiny arachnids feed on the plant tissues, causing stippling, yellowing, and webbing on the leaves. Severe infestations can lead to leaf drop and reduced plant vigor.',
 34:'Target spot is a fungal disease that affects tomato plants. It is caused by the pathogen Corynespora cassiicola. The disease causes circular lesions with a concentric ring pattern on the leaves, stems, and fruit of tomato plants. Infected tissues may turn yellow or necrotic. Target spot can lead to defoliation and yield losses under favorable conditions.',
 35:'Tomato yellow leaf curl virus (TYLCV) is a viral disease that affects tomato plants. It is transmitted by whiteflies. The disease causes curling and yellowing of the leaves, stunted growth, and reduced yield. TYLCV can severely impact tomato production, particularly in regions with high whitefly populations.',
 36:'Tomato mosaic virus (ToMV) is a viral disease that affects tomato plants. It is transmitted through contact with infected plant sap or contaminated tools. The disease causes mottling, distortion, and yellowing of the leaves. Infected fruits may show mosaic patterns and reduced quality. ToMV can spread rapidly in greenhouse and field environments.',
 37:'The "Tomato Healthy" category represents healthy tomato plants without any apparent diseases or disorders. The leaves appear normal and show no signs of infection or damage.'

}

Remedy_name = {

0:":Choose resistant varieties when possible. Rake under trees and destroy infected leaves to reduce the number of fungal spores available to start the disease cycle over again next spring. Water in the evening or early morning hours (avoid overhead irrigation) to give the leaves time to dry out before infection can occur.",
 1:'getting rid of these sources of fungal infection.  This is the primary method of control. Remove the cankers by pruning at least 15 inches below the end and burn or bury them.  Also take preventative care with new season prunings and burn them, too',
 2:'Choose resistant cultivars when available. Rake up and dispose of fallen leaves and other debris from under trees. Remove galls from infected junipers. In some cases, juniper plants should be removed entirely.',
 3:'Healthy leaf do not require any treatment',
 4:'Healthy leaf do not require any treatment',
 5:'The key to managing powdery mildew on the fruit is to keep the disease off of the leaves.  Most synthetic fungicides are preventative, not eradicative, so be pro-active about disease prevention.  Maintain a consistent program from shuck fall through harvest. ',
 6:'Healthy leaf do not require any treatment',
 7:'Plant corn hybrids with resistance to the disease; crop rotation and plowing debris into soil may reduce levels of inoculum in the soil but may not provide control in areas where the disease is prevalent; foliar fungicides may be economically viable for some high yeilding susceptible hybrids',
 8:'The most effective method of controlling the disease is to plant resistant hybrids; application of appropriate fungicides may provide some degree on control and reduce disease severity; fungicides are most effective when the amount of secondary inoculum is still low, generally when plants only have a few rust pustules per leaf.',
 9:'Follow proper tillage to reduce fungus inoculum from crop debris. Follow crop rotation with non host crop. Grow available resistant varieties. In severe case of disease incidence apply suitable fungicide.',
 10:'Healthy leaf do not require any treatment',
 11:'To treat grape black rot, it is important to apply fungicides specifically labeled for black rot control in grapes. Follow the recommended application schedule and dosage as per the product label. Pruning is also essential to remove infected grape clusters, shoots, and leaves. Proper sanitation practices, such as cleaning up fallen leaves and debris, help reduce overwintering sources of black rot. Additionally, maintaining an open canopy through proper training and trellising promotes better air circulation and sunlight penetration, reducing humidity and improving grapevine health.',
 12:'Treating grape esca involves pruning and removing the wood with characteristic symptoms of the disease, such as dark streaking and discoloration. Infected grape clusters and canes should be removed and destroyed. Good sanitation practices, including the removal of fallen leaves, debris, and mummified berries, help minimize disease spread. Applying appropriate wound protectants or fungicides to pruning wounds or damaged areas can prevent infection by esca pathogens. Proper canopy management, maintaining the right density and avoiding excessive vine vigor, also plays a crucial role in managing esca.',
 13:'Treating grape leaf blight requires the application of fungicides labeled for leaf blight control in grapes. Follow the recommended application schedule and dosage as per the product label, particularly during the growing season when conditions are favorable for disease development. Pruning should be conducted during the dormant season to remove infected leaves and canes, promoting good air circulation. Sanitation practices, including the removal and destruction of infected plant debris, fallen leaves, and mummified berries, help reduce disease inoculum. Proper canopy management through pruning assists in improving sunlight penetration and air circulation, reducing leaf wetness and the likelihood of disease development.',
 14:'Healthy leaf do not require any treatment',
 15:'To treat orange trees affected by Haunglongbing, it is crucial to implement an integrated pest management approach. This includes regular monitoring and early detection of infected trees. Infected trees should be promptly removed and destroyed to prevent further spread. Insect vectors, such as the Asian citrus psyllid, should be controlled through the application of appropriate insecticides. Nutritional management is essential, including the use of balanced fertilizers and foliar nutrient sprays to support tree health and minimize the impact of the disease. It is also important to practice good sanitation, such as removing fallen leaves and debris, and ensure proper irrigation and drainage to reduce stress on the trees.',
 16:'Treating peach trees affected by bacterial spot involves several measures. Cultural practices such as pruning, thinning, and maintaining proper tree spacing help to promote good air circulation and reduce disease severity. Copper-based fungicides or bactericides can be applied during dormancy and before bud break to control bacterial spot. During the growing season, protectant copper sprays or bactericides can be used to suppress disease development. It is crucial to follow the recommended application rates and timings as per the product label. Proper sanitation, including the removal and destruction of infected plant debris, also helps reduce disease inoculum. Regular monitoring and early detection of symptoms are key to implementing timely treatments and managing peach bacterial spot effectively.',
 17:'Healthy leaf do not require any treatment',
 18:'Treating pepper plants affected by bacterial spot involves a combination of cultural and chemical measures. To manage this disease, remove and destroy infected plant material to prevent further spread. Avoid overhead irrigation and water the plants at the base to reduce leaf wetness. Copper-based fungicides or bactericides can be applied as a preventive measure, following the recommended application schedule and dosage. Additionally, ensure proper spacing between plants to promote air circulation and reduce humidity, which can inhibit disease development.',
 19:'Healthy leaf do not require any treatment',
 20:'Managing early blight in potato plants requires a multi-faceted approach. Remove and destroy infected plant parts, especially affected leaves, to prevent the spread of the disease. Apply fungicides labeled for early blight control, following the recommended application schedule and dosage as per the product label. Proper crop rotation is important to reduce disease pressure, as well as planting resistant potato varieties. Good soil management, including balanced fertilization and proper irrigation practices, can also help maintain plant health and reduce the impact of early blight',
 21:'Treating late blight in potato plants involves several strategies. Remove and destroy infected plant material immediately to prevent further disease spread. Apply fungicides specifically labeled for late blight control, following the recommended application schedule and dosage as per the product label. Implement proper irrigation practices, such as avoiding overhead watering and providing sufficient drainage, to reduce leaf wetness and humidity. Plant resistant potato varieties if available. Regular monitoring and early detection of symptoms are crucial for timely management of late blight.',
 22:'Healthy leaf do not require any treatment',
 23:'Healthy leaf do not require any treatment',
 24:'Healthy leaf do not require any treatment',
 25:'Managing powdery mildew in squash plants includes various approaches. Implement cultural practices such as proper plant spacing and pruning to enhance air circulation and reduce humidity. Avoid overhead irrigation and water the plants at the base to keep the leaves dry. Apply fungicides labeled for powdery mildew control, following the recommended application schedule and dosage as per the product label. Regularly monitor the plants for signs of infection and take prompt action to control the disease. Removing and disposing of infected plant material can also help prevent the spread of powdery mildew.',
 26:'Treating strawberry plants affected by leaf scorch requires a combination of cultural and chemical methods. Practice good sanitation by removing and destroying infected plant material. Ensure proper spacing between plants to allow for air circulation. Apply fungicides labeled for leaf scorch control, following the recommended application schedule and dosage as per the product label. Adequate irrigation and soil moisture management can help maintain plant health and minimize the impact of the disease. Regular monitoring and early detection of symptoms are crucial for effective management of strawberry leaf scorch.',
 27:'Healthy leaf do not require any treatment',
 28:'Managing bacterial spot in tomato plants involves a multi-faceted approach. Remove and destroy infected plant parts to prevent the spread of the disease. Apply copper-based bactericides or other appropriate products labeled for bacterial spot control, following the recommended application schedule and dosage. Implement proper irrigation practices, such as avoiding overhead watering and providing sufficient drainage, to reduce leaf wetness. Proper spacing between tomato plants and good air circulation can help inhibit disease development. Planting resistant tomato varieties can also be beneficial in managing bacterial spot.',
 29:'Treating early blight in tomato plants requires a comprehensive approach. Remove and destroy infected plant material to minimize disease spread. Apply fungicides specifically labeled for early blight control, following the recommended application schedule and dosage as per the product label. Implement proper irrigation practices, such as avoiding overhead watering and providing adequate soil drainage. Maintaining good plant spacing and airflow can help reduce humidity and minimize disease development. Regular monitoring and early detection of symptoms are essential for timely treatment and management.',
 30:'Managing late blight in tomato plants involves several measures. Remove and destroy infected plant parts, including affected leaves and fruit, to prevent further disease spread. Apply fungicides labeled for late blight control, following the recommended application schedule and dosage as per the product label. Ensure proper irrigation practices, avoiding overhead watering and providing sufficient drainage to reduce leaf wetness. Good plant spacing and airflow help reduce humidity and minimize disease development. Timely and regular monitoring of plants is crucial for effective management of late blight.',
 31:'Treating leaf mold in tomato plants requires a combination of cultural and chemical methods. Remove and destroy infected leaves to prevent disease spread. Increase spacing between plants to enhance air circulation and reduce humidity. Apply fungicides labeled for leaf mold control, following the recommended application schedule and dosage as per the product label. Proper irrigation practices, such as watering at the base and avoiding overhead irrigation, can help minimize leaf wetness. Regular monitoring and early detection of symptoms are important for timely treatment and management of tomato leaf mold.',
 32:'Managing septoria leaf spot in tomato plants involves a multi-faceted approach. Remove and destroy infected leaves and debris to prevent further disease spread. Apply fungicides specifically labeled for septoria leaf spot control, following the recommended application schedule and dosage as per the product label. Implement proper irrigation practices, such as watering at the base and avoiding leaf wetness. Good plant spacing and airflow can help reduce humidity and minimize disease development. Regular monitoring and early detection of symptoms are vital for effective management of septoria leaf spot.',
 33:'Tomato___Spider_mites Two-spotted_spider_mite',
 34:'To manage target spot in tomato plants, it is important to remove and destroy infected plant material to prevent disease spread. Implement proper irrigation practices, such as watering at the base and avoiding overhead irrigation, to minimize leaf wetness. Apply fungicides labeled for target spot control, following the recommended application schedule and dosage as per the product label. Good plant spacing and airflow can help reduce humidity and disease development. Regular monitoring and early detection of symptoms are crucial for timely treatment and effective management of target spot in tomatoes',
 35:'Managing tomato plants affected by tomato yellow leaf curl virus (TYLCV) involves a combination of cultural and chemical measures. To prevent the spread of TYLCV, it is important to control the whitefly vectors that transmit the virus. This can be done through the application of insecticides specifically targeting whiteflies. Planting resistant tomato varieties can also be helpful in reducing the impact of the virus. Proper sanitation practices, including the removal and destruction of infected plants, can help minimize disease spread. Regular monitoring of plants and immediate removal of any infected individuals can further aid in managing TYLCV.',
 36:'Treating tomato mosaic virus (ToMV) involves several strategies. Start by removing and destroying infected plants to prevent further disease spread. Practice good sanitation by washing hands and tools thoroughly after handling infected plants, as ToMV can be easily transmitted. Implement insect control measures to prevent aphids, thrips, or whiteflies from spreading the virus. Additionally, select virus-resistant tomato varieties when available. Disinfecting greenhouse structures and equipment is crucial to prevent the virus from persisting. Proper crop rotation and weed control are also important to reduce reservoirs of the virus in the surrounding environment.',
 37:'Healthy leaf do not require any treatment'
}
spacy_model = spacy.load("en_core_web_sm")

#bot = ChatBot("ChatBOT", read_only=False, logic_adapters=[{"import_path":"chatterbot.logic.BestMatch","default_response":"Sorry, I don't have an answer yet, Meet a professional","maximum_similarity_threshold":0.9}])

#list_to_train = ["Tomato mosaic virus","The disease causes mottling, distortion, and yellowing of the leaves. Infected fruits may show mosaic patterns and reduced quality. ToMV can spread rapidly in greenhouse and field environments","What can be the solution to cure tomato mosaic virus","Use Papso3 fertilizer"]
#list_to_train1 = ["Tomato Septoria leaf spot","it is important to remove and destroy infected plant material to prevent disease spread. Implement proper irrigation practices, such as watering at the base and avoiding overhead irrigation"]
#list_to_train2 = ["Apple black rot","pruning out young shoots infected with fire blight during late spring and removing mummified fruit helps minimize sources of black rot inoculum","Apple scab" ,"Planting disease resistant varieties is the best way to manage scab. Fungicides can be used to manage apple scab. Proper timing of sprays is needed for fungicides to control disease.","Cedar apple rust","Fungicides with the active ingredient Myclobutanil are most effective in preventing rust. Copper and sulfur products can be used as well. Spray trees and shrubs when flower buds first emerge until spring weather becomes consistently warm and dry."]
#list_to_train3 = ["Esca (Black_Measles) in grape plant leaf","Esca, also known as black measles, is a complex fungal disease that affects grapevines. It is caused by several pathogens, including Phaeomoniella chlamydospora"]
#list_to_train4 = ["Powdery mildew cherry","A well pruned canopy will promote more air flow and leaf drying, reducing these humid conditions favorable for disease. Pruning will also help to achieve good spray coverage.","Cercospora leaf spot corn" ,"Burying the debris under the last year's crop will help in reducing the presence of Cercospora zeae-maydis, as the fungal-infected debris can only survive above the soil surface."]
#list_to_train5 = ["Corn common rust","Numerous fungicides are available for rust control. Products containing mancozeb, pyraclostrobin, pyraclostrobin + metconazole, pyraclostrobin + fluxapyroxad, azoxystrobin + propiconazole, trifloxystrobin + prothioconazole can be used to control the disease.","Corn Northern blight" ,"A one-year rotation away from corn, followed by tillage is recommended to prevent disease development in the subsequent corn crop."]
#list_to_train6 = ["Black rot grape","Removing mummies from the vineyard is helpful to prevent the spread of fungal spores. Thinning the canopy by pulling leaves and shoot thinning help to improve air-flow circulation","Grape leaf blight" ,"Spraying of the grapevines at 3-4 leaf stage with fungicides like Bordeaux mixture @ 0.8% or Copper Oxychloride @ 0.25% or Carbendazim @ 0.1% are effective against this disease."]
#list_to_train7 = ["Orange Huanglongbing","prevent the spread of the HLB pathogen by controlling psyllid populations and destroying any infected trees.","Bacterial spot peach" ,"Early season pruning can help control tree vigor, and summer pruning can improve air movement and increase sunlight penetration to improve fruit ripening."]
#list_to_train8 = ["Bacterial spot pepper","use of certified pathogen-free seed and disease-free transplants. The bacteria do not survive well once host material has decayed, so crop rotation is recommended.","leaf scorch strawberry" ,"The avoidance of waterlogged soil and frequent garden cleanup will help to reduce the likelihood of spread of this fungus."]
#list_to_train9 = ["Early blight potato","Early blight can be minimized by maintaining optimum growing conditions, including proper fertilization, irrigation, and management of other pests","Late blight potato" ,"Late blight is controlled by eliminating cull piles and volunteer potatoes, using proper harvesting and storage practices, and applying fungicides when necessary."]
#list_to_train10 = ["Bacterial spot tomato","Use drip irrigation and avoid overhead irrigation if possible. Water plants in the morning to allow water on plants to evaporate quickly. Avoid handling plants while plants are wet.","Early blight tomato" ,"Prune the bottom most leaves as the plant grows. These leaves are usually more infected than the upper parts of the plant."]
#list_to_train11 = ["Late blight tomato","Avoid planting tomatoes on sites that were previously in potatoes or close to potatoes. Sequential planting or planting several crops of tomatoes over time will reduce the risk","" ,""]
#list_to_train12 = ["Leaf mold tomato","Monitor for disease and rogue infected plants as soon as detected. Avoid excessive nitrogen fertilization","Spider mite tomato" ,"Apply water to pathways and other dusty areas at regular intervals. Water-stressed trees and plants are less tolerant of spider mite damage."]
#list_to_train13 = ["Tomato target spot","Remove old plant debris at the end of the growing season; otherwise, the spores will travel from debris to newly planted tomatoes","Yellow leaf curl virus" ,"Control the whitefly population to avoid the infection with the virus. Insecticides of the family of the pyrethroids used as soil drenches or spray during the seedling stage can reduce the population of whiteflies."]


#list_trainer = ListTrainer(bot)

#list_trainer.train(list_to_train)
#list_trainer.train(list_to_train1)
#list_trainer.train(list_to_train2)
#list_trainer.train(list_to_train3)
#list_trainer.train(list_to_train4)
#list_trainer.train(list_to_train5)
#list_trainer.train(list_to_train6)
#list_trainer.train(list_to_train7)
#list_trainer.train(list_to_train8)
#list_trainer.train(list_to_train9)
#list_trainer.train(list_to_train10)
#list_trainer.train(list_to_train11)
#list_trainer.train(list_to_train12)
#list_trainer.train(list_to_train13)


#trainer = ChatterBotCorpusTrainer(bot)
#trainer.train("chatterbot.corpus.english")
'''
while True:
    user_response = input("User: ")
    print(bot.get_response(user_response))

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/get')
def get_chatbot_response():
    print('Nehal')
    userText = request.args.get('userMessage')
    return str(bot.get_response(userText))'''

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')

model = load_model('plants.h5')
REC_MODEL = pickle.load(open(os.path.join(MODEL_DIR, 'RF.pkl'), 'rb'))

def predict_label(img_path):
	test_image = image.load_img(img_path, target_size=(224,224))
	test_image = image.img_to_array(test_image)/255.0
	test_image = test_image.reshape(1, 224,224,3)

	predict_x=model.predict(test_image) 
	classes_x=np.argmax(predict_x,axis=1)
	
	return Disease_name[classes_x[0]]

def predict_content(img_path):
	test_image = image.load_img(img_path, target_size=(224,224))
	test_image = image.img_to_array(test_image)/255.0
	test_image = test_image.reshape(1, 224,224,3)

	predict_x=model.predict(test_image) 
	classes_x=np.argmax(predict_x,axis=1)
	
	return Content_name[classes_x[0]]

def remedy_content(img_path):
	test_image = image.load_img(img_path, target_size=(224,224))
	test_image = image.img_to_array(test_image)/255.0
	test_image = test_image.reshape(1, 224,224,3)

	predict_x=model.predict(test_image) 
	classes_x=np.argmax(predict_x,axis=1)
	
	return Remedy_name[classes_x[0]]

def ProcessImage(image, processing_factor):
    # Read image from BytesIO
    nparr = np.frombuffer(image, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Split channels
    b, g, r = cv2.split(img)

    # Calculate disease channel
    disease = r - g

    # Calculate alpha channel
    alpha = np.where((img[..., 0] > 200) & (img[..., 1] > 200) & (img[..., 2] > 200), 255, 0)

    # Apply processing factor
    disease = np.where(g > processing_factor, 255, disease)

    # Calculate disease percentage
    count = np.count_nonzero(alpha == 0)
    res = alpha.size
    percent = (np.count_nonzero(disease < processing_factor) / count) * 100

    # Encode images to base64
    _, disease_data = cv2.imencode('.png', disease)
    disease_base64 = base64.b64encode(disease_data).decode('utf-8')

    _, b_data = cv2.imencode('.png', b)
    b_base64 = base64.b64encode(b_data).decode('utf-8')

    _, g_data = cv2.imencode('.png', g)
    g_base64 = base64.b64encode(g_data).decode('utf-8')

    _, alpha_data = cv2.imencode('.png', alpha)
    alpha_base64 = base64.b64encode(alpha_data).decode('utf-8')

    _, r_data = cv2.imencode('.png', r)
    r_base64 = base64.b64encode(r_data).decode('utf-8')
    

    return disease_base64, percent, b_base64, g_base64, alpha_base64, r_base64

 
@app.route("/")
@app.route("/first")
def first():
	return render_template('first.html')

@app.route("/register")
def register():
	return render_template('register.html')
   

@app.route("/login")
def login():
	return render_template('login.html')   

@app.route('/loginaction', methods=['POST'])
def loginaction():
    msg=""
    username = request.form['uname']
    password = request.form['pwd']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM reg WHERE username = %s and password = %s', (username,password,))
    account = cursor.fetchone()
    if account:
        msg="login success"
        flash("login success")
        return render_template('upload.html', account=account, msg=msg)
    else:
        msg = "Invalid Credentials"
        flash("Invalid Credentials")
        return render_template('login.html', msg=msg)
    
@app.route("/index", methods=['GET', 'POST'])
def index():
	return render_template("index.html")

@app.route('/health', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        if 'file' not in request.files:
            return render_template('health.html', error='No file selected.')

        file = request.files['file']
        if file.filename == '':
            return render_template('health.html', error='No file selected.')

        # Read the image file from the request
        image = file.read()

        processing_factor = int(request.form['factor'])

        # Process the image
        disease_image, disease_percentage, b_channel, g_channel, alpha_channel, r_channel = ProcessImage(image,
                                                                                                          processing_factor)
		 
		
	
        return render_template('health.html',  disease_image=disease_image, percentage=disease_percentage,
                               b_channel=b_channel, g_channel=g_channel, alpha_channel=alpha_channel,
                               r_channel=r_channel)

    return render_template('health.html')






@app.route("/submit", methods = ['GET', 'POST'])
def get_output():
	if request.method == 'POST':
		img = request.files['my_image']

		img_path = "static/tests/" + img.filename	
		img.save(img_path)

		predict_result = predict_label(img_path)
		predict_c = predict_content(img_path)
		remedy = remedy_content(img_path)
	return render_template("prediction.html", prediction = predict_result, pred = predict_c ,remedy = remedy, img_path = img_path)

@app.route("/performance")
def performance():
	return render_template('performance.html')
    
@app.route("/chart")
def chart():
	return render_template('chart.html') 




	
if __name__ =='__main__':
	app.run(debug = True)


	

	


