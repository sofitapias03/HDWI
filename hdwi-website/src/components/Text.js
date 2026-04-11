import React from 'react'
import '../styles/text.css'

function Text () {
    return(
        <div className = 'text'>
        <h2> What is HDWI?</h2>
        <p>
        The Hot-Dry-Windy Index (HDWI) is a way scientists and fire 
        managers estimate how favorable the atmosphere is for wildfire 
        growth and spread. In simple terms, it combines three important 
        ingredients that strongly influence fire behavior: heat, dryness in 
        the air, and wind speed. When temperatures are high, vegetation and 
        fuels like grass or forest litter can dry out more quickly. At the same 
        time, low humidity means the air can pull moisture away from those fuels, 
        making them easier to ignite. Wind is the third piece of the puzzle because 
        it can both supply oxygen to a fire and push flames across the landscape, helping 
        a fire expand faster. HDWI attempts to bring these conditions together into a single 
        value that describes how “fire-friendly” the weather is at a given place and time. 🔥🌬️🌡️
        </p>
        <h2>What is Paragon?</h2>
        <p>
        Paragon is a student-led group within Enactus University of Calgary at University of 
        Calgary that focuses on wildfire-related challenges and data-driven solutions. The team 
        works on projects involving wildfire risk awareness, the Hot-Dry-Windy Index (HDWI), 
        and the development of models that help analyze and predict conditions that could contribute 
        to wildfire growth. By combining technology, research, and collaboration, Paragon aims to turn 
        complex environmental data into tools and visualizations that make wildfire information easier 
        to understand and use.
        </p>

        </div>
    )
}

export default Text;