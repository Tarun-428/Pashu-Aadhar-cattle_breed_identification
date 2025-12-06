import os
import numpy as np
import logging
import traceback
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.resnet50 import preprocess_input

# Disable TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Configure logging
logging.basicConfig(level=logging.INFO)

class CattleBreedClassifier:
    def __init__(self, model_path, class_names=None):
        self.model = None
        self.class_names = class_names if class_names else ["Gir", "Holstein_Friesian", "Jaffrabadi", "Jersey", "Murrah", "Sahiwal"]
        self.load_model(model_path)
    
    def load_model(self, model_path):
        """Load custom-trained ResNet50 model"""
        try:
            if os.path.exists(model_path):
                self.model = tf.keras.models.load_model(model_path)
                logging.info(f"✅ Custom ResNet50 model loaded from: {model_path}")
                logging.info(f"✅ Model output shape: {self.model.output_shape}")
            else:
                logging.error(f"❌ Model file not found at: {model_path}")
                self.model = None
        except Exception as e:
            logging.error(f"❌ Error loading model: {str(e)}")
            logging.error(traceback.format_exc())
            self.model = None
    
    def preprocess_image(self, image_path):
        """Preprocess image for prediction"""
        try:
            img = Image.open(image_path).convert('RGB')
            img = img.resize((224, 224))
            
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            
            return img_array
            
        except Exception as e:
            logging.error(f"❌ Error preprocessing image: {str(e)}")
            logging.error(traceback.format_exc())
            return None
    
    def predict(self, image_path):
        """Predict cattle breed from image"""
        if self.model is None:
            logging.error("❌ Model is not loaded.")
            return None
        
        try:
            processed_image = self.preprocess_image(image_path)
            if processed_image is None:
                return None
            
            predictions = self.model.predict(processed_image, verbose=0)
            
            if predictions.shape[1] != len(self.class_names):
                logging.warning(f"⚠ Model output classes ({predictions.shape[1]}) "
                                f"do not match provided class names ({len(self.class_names)})")
            
            predicted_class_idx = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class_idx])
            predicted_breed = self.class_names[predicted_class_idx] if predicted_class_idx < len(self.class_names) else f"Class_{predicted_class_idx}"
            
            return {
                'breed': predicted_breed,
                'confidence': confidence,
                'all_predictions': {
                    (self.class_names[i] if i < len(self.class_names) else f"Class_{i}"): float(predictions[0][i])
                    for i in range(predictions.shape[1])
                }
            }
            
        except Exception as e:
            logging.error(f"❌ Error during prediction: {str(e)}")
            logging.error(traceback.format_exc())
            return None


# ✅ Path to your custom ResNet50 model
MODEL_PATH = 'resnet50_model.h5'

# ✅ Global classifier instance
classifier = CattleBreedClassifier(MODEL_PATH)

def predict_breed(image_filename):
    """Main function to predict breed from uploaded image"""
    try:
        image_path = os.path.join('static/uploads', image_filename)
        
        if not os.path.exists(image_path):
            logging.error(f"❌ Image file not found: {image_path}")
            return None
        
        result = classifier.predict(image_path)
        
        if result:
            logging.info(f"✅ Prediction result: {result['breed']} "
                         f"with confidence {result['confidence']:.2f}")
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Error in predict_breed: {str(e)}")
        logging.error(traceback.format_exc())
        return None
