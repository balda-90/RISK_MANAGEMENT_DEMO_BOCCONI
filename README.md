# Automotive Risk Assessment Application

An intelligent risk assessment tool for the automotive industry, powered by AI agents and voice commands.

## Overview

This application provides a comprehensive risk assessment framework for automotive industry projects at three levels:

1. **Strategic Level**: Assessing high-level risks related to product ranges and market strategies
2. **Project Level**: Evaluating risks for specific vehicle projects and shared components
3. **Operational Level**: Detailed risk assessment for sub-components and technical implementations

The application leverages AI agents to automatically gather, evaluate, and suggest mitigation strategies for potential risks, creating a powerful tool for risk management in automotive development.

## Features

- **Multi-level Risk Assessment**: Strategic, Project, and Operational risk evaluation
- **AI-Powered Risk Generation**: Automated identification of common risks based on project context
- **Risk Evaluation**: AI-assisted probability, cost, and time impact assessment
- **Mitigation Planning**: AI-generated mitigation strategies for identified risks
- **Voice Command Interface**: Control the application using natural language voice commands
- **Rich Visualization**: Interactive dashboards and charts to visualize risk distribution and impact
- **Customizable Configuration**: Configure AI agents' behavior to match your risk assessment needs

## AI Agent Architecture

The application uses a team of specialized AI agents:

1. **Web Search Agent**: Identifies common risks related to automotive projects and components
2. **Risk Evaluation Agent**: Assesses probability, cost impact, and time impact of identified risks
3. **Mitigation Planning Agent**: Creates comprehensive mitigation plans for each risk

These agents are coordinated by an Agent Coordinator which manages the workflow and interaction between agents.

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (for AI agent functionality)
- Microphone (for voice command functionality)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd automotive-risk-assessment
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your OpenAI API key:
   - Create a `.env` file in the project root
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

### Running the Application

Start the application with:

```
streamlit run app.py
```

The application will be available at http://localhost:8501 by default.

## Usage

### Web Interface

The application provides a streamlined web interface with the following sections:

- **Dashboard**: Overview of risk assessment with visualizations
- **Risk Management**: Detailed risk table and form for adding/editing risks
- **AI Agent Configuration**: Settings for the AI agents
- **Voice Commands**: Interface for voice command functionality

### Voice Commands

You can control the application using voice commands such as:

- "Generate risk assessment"
- "Show dashboard"
- "Filter by strategic level"
- "Show top risks"
- "Save the data"

## Project Structure

```
automotive-risk-assessment/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
├── README.md                   # This documentation
├── agents/                     # AI agent modules
│   └── agent_coordinator.py    # Agent coordination logic
├── voice_commands/             # Voice processing modules
│   └── voice_processor.py      # Voice command handling
├── data/                       # Data storage
│   ├── initial_data.json       # Initial project data
│   └── risk_assessment_data.json  # Generated risk assessments
└── config/                     # Configuration files
    └── agent_config.json       # AI agent configuration
```

## Customization

### Adding New Project Data

Edit the `data/initial_data.json` file to add your product ranges, projects, and components.

### Configuring AI Agents

Use the AI Agent Configuration page in the application to adjust agent parameters such as temperature (creativity) and enable/disable specific agents.

## License

[MIT License](LICENSE)

## Acknowledgements

- OpenAI for providing the API powering the AI agents
- Streamlit for the web application framework 