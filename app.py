from flask import Flask, request, render_template
import re
import os
from openai import OpenAI # Import the OpenAI library
import uuid
from werkzeug.utils import secure_filename


app = Flask(__name__)

# List of predefined countries, colors, shapes, and styles
countries_list = [
    "India", "USA", "China", "Germany", "France", "Japan", "Italy", "UK", "Canada", "Australia"
]

colors_list = [
    "red", "blue", "green", "yellow", "black", "white", "gray", "purple", "pink", "orange", "brown", "beige"
]

shapes_list = [
    "round", "square", "rectangle", "oval", "triangle", "hexagon", "octagon"
]

styles_list = [
    "modern", "antique", "classy", "vintage", "contemporary", "rustic", "minimalistic", "traditional"
]

additional_features_list = [
    "eco-friendly", "lightweight", "sustainable", "durable", "waterproof", 
    "breathable", "versatile", "washable", "comfortable", "recyclable", 
    "compact", "adjustable", "stylish", "modern", "vintage", "soft", 
    "organic", "reversible", "high-quality", "portable", "hypoallergenic", 
    "fashionable", "stretchable", "moisture-wicking", "slim-fit", "easy-care", 
    "functional", "luxurious", "machine-washable", "non-toxic", "sleek", 
    "antibacterial", "temperature-regulating"
]

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)


# Function to extract additional features from the caption
def extract_additional_features(caption):
    features = []
    caption = caption.lower()  # Convert caption to lowercase for case-insensitive comparison
    for feature in additional_features_list:
        if feature in caption:
            features.append(feature.capitalize())  # Capitalize the feature for consistency
    return features if features else ["No special features"]

# Function to extract price from the caption
def extract_price(caption):
    price_match = re.search(r'₹([\d,]+)', caption)  # Searching for ₹ symbol followed by numbers (with commas)
    if price_match:
        price_str = price_match.group(1)
        price_str = price_str.replace(',', '')  # Remove commas for proper price extraction
        return '₹' + price_str
    return "  "

# Function to extract country from the caption (case-insensitive)
def extract_country(caption):
    caption = caption.lower()  # Convert caption to lowercase for case-insensitive comparison
    for country in countries_list:
        if country.lower() in caption:
            return country
    return "  "

# Function to extract color from the caption
def extract_color(caption):
    caption = caption.lower()
    for color in colors_list:
        if color in caption:
            return color.capitalize()  # Capitalize the color for consistency
    return "  "

# Function to extract shape from the caption
def extract_shape(caption):
    caption = caption.lower()
    for shape in shapes_list:
        if shape in caption:
            return shape.capitalize()  # Capitalize the shape for consistency
    return "  "

# Function to extract style from the caption
def extract_style(caption):
    caption = caption.lower()
    for style in styles_list:
        if style in caption:
            return style.capitalize()  # Capitalize the style for consistency
    return "  "

# Function to generate AI description based on the caption
def generate_ai_description(caption):
    try:
        # Sending the user's caption to OpenAI for AI-based description generation
        completion = client.chat.completions.create(
            model="meta/llama-3.1-405b-instruct",
            messages=[{"role": "user", "content": f"Generate a product description for {caption}"}],
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=True  # Stream the response
        )

        ai_description = ""
        
        # Process each chunk of the streamed response
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                ai_description += chunk.choices[0].delta.content  # Accumulate the content from the chunks
        

        ai_description = ai_description.replace('*', '')

        return ai_description
    
    except Exception as e:
        return f"Error generating description: {e}"



# Route to display the upload form
@app.route('/')
def index():
    return render_template('index.html')

# Route to process the uploaded image and caption
@app.route('/process', methods=['POST'])
def process():
    if 'image' not in request.files or 'caption' not in request.form:
        return "No image or caption provided", 400
    
    image = request.files['image']
    caption = request.form['caption']

    # Validate file type
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in image.filename and image.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
        return "Invalid file type. Only images are allowed.", 400

    # Save the uploaded image to the 'uploads' folder with a unique name
    filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
    image_path = os.path.join('static', 'uploads', filename)
    image.save(image_path)

    # Extract details
    price = extract_price(caption)
    country = extract_country(caption)
    color = extract_color(caption)
    shape = extract_shape(caption)
    style = extract_style(caption)

    additional_features = extract_additional_features(caption)
    # Generate AI-based product description
    ai_description = generate_ai_description(caption)

    # Create the product listing with all extracted details and AI description
    product_listing = {
        "image": image.filename,
        "description": caption,
        "ai_description": ai_description,  # Adding AI description
        "price": price,
        "country_of_origin": country,
        "color": color,
        "shape": shape,
        "style": style,
        "additional_features": ", ".join(additional_features) 
    }

    return render_template('index.html', result=product_listing)

if __name__ == '__main__':
    # Create 'uploads' folder if it doesn't exist
    if not os.path.exists(os.path.join('static', 'uploads')):
        os.makedirs(os.path.join('static', 'uploads'))
    
    app.run(debug=True)
