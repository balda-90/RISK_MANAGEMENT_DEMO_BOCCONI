import os
import json
from pathlib import Path
from typing import List, Dict, Any
import time
from datetime import datetime
import random
from dotenv import load_dotenv

# Try to load OpenAI from langchain first, if not available, import directly
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import Tool, AgentExecutor, create_openai_functions_agent
    from langchain.agents.format_scratchpad import format_to_openai_functions
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.memory import ConversationBufferMemory
    from langchain.tools import StructuredTool
    from langchain_core.messages import AIMessage, HumanMessage
except ImportError:
    # Fallback to direct OpenAI import if langchain is not available
    import openai
    
# Load environment variables
load_dotenv()

class WebSearchAgent:
    """Agent responsible for web search to find common automotive risks"""
    
    def __init__(self, temperature=0.7):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        
        # Initialize OpenAI client
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=temperature,
                api_key=self.openai_api_key
            )
        except Exception as e:
            print(f"Error initializing WebSearchAgent: {e}")
            self.llm = None
    
    def search_risks(self, project_type: str, project_name: str, component_name: str = None) -> List[Dict]:
        """
        Search for common risks related to an automotive project or component
        
        Args:
            project_type: Type of project (strategic, project, operational)
            project_name: Name of the project or range
            component_name: Name of the component (if applicable)
            
        Returns:
            List of dictionaries containing risk information
        """
        if not self.llm:
            # Return some mock data if OpenAI is not available
            return self._generate_mock_risks(project_type, project_name, component_name)
        
        # Prepare the prompt
        search_target = f"{project_name} {component_name or ''} in automotive industry".strip()
        system_prompt = f"""You are an expert in automotive risk assessment. 
        Identify the most common risks for {project_type} level issue: {search_target}.
        Focus on real risks in the automotive industry. For each risk, provide:
        1. A short title
        2. A detailed description
        3. An estimated probability (0.0-1.0)
        4. Potential cost impact
        5. Potential time impact (in weeks)
        6. Detection difficulty (0.0-1.0)
        7. A potential mitigation plan
        
        Return 3-5 most critical risks in a structured format."""
        
        try:
            # Generate response
            result = self.llm.invoke(system_prompt)
            
            # Parse the response into structured risk data
            risks = self._parse_risk_response(result.content, project_type, project_name, component_name)
            return risks
            
        except Exception as e:
            print(f"Error in web search: {e}")
            # Fallback to mock data if the API call fails
            return self._generate_mock_risks(project_type, project_name, component_name)
    
    def _parse_risk_response(self, response: str, project_type: str, project_name: str, component_name: str = None) -> List[Dict]:
        """Parse the LLM response into structured risk data"""
        risks = []
        
        try:
            # Split the response by numbered items or headers
            sections = response.split("\n\n")
            current_risk = {}
            
            for section in sections:
                if "Risk" in section and ":" in section and not current_risk:
                    # Start of a new risk
                    title_parts = section.split(":", 1)
                    if len(title_parts) > 1:
                        current_risk = {
                            "Risk_ID": f"R{len(risks) + 1}",
                            "Level": project_type.lower(),
                            "Project": component_name or project_name,
                            "Risk_Title": title_parts[1].strip(),
                            "Owner": "",  # To be filled by user
                        }
                
                if current_risk:
                    # Extract risk details
                    if "Description" in section:
                        current_risk["Risk_Description"] = section.split(":", 1)[1].strip() if ":" in section else section
                    elif "Probability" in section:
                        prob_text = section.split(":", 1)[1].strip() if ":" in section else "0.5"
                        # Extract numeric value from text
                        prob_value = next((float(s) for s in prob_text.split() if s.replace('.', '', 1).isdigit()), 0.5)
                        current_risk["Risk_Probability"] = min(max(prob_value, 0.0), 1.0)  # Ensure in range 0-1
                    elif "Cost" in section and "Impact" in section:
                        cost_text = section.split(":", 1)[1].strip() if ":" in section else "100000"
                        # Extract numeric value
                        cost_value = ''.join(filter(lambda x: x.isdigit(), cost_text)) or "100000"
                        current_risk["Cost_Impact"] = int(cost_value)
                    elif "Time" in section and "Impact" in section:
                        time_text = section.split(":", 1)[1].strip() if ":" in section else "4"
                        # Extract numeric value
                        time_value = next((int(s) for s in time_text.split() if s.isdigit()), 4)
                        current_risk["Time_Impact"] = time_value
                    elif "Detection" in section:
                        det_text = section.split(":", 1)[1].strip() if ":" in section else "0.5"
                        # Extract numeric value
                        det_value = next((float(s) for s in det_text.split() if s.replace('.', '', 1).isdigit()), 0.5)
                        current_risk["Detection"] = min(max(det_value, 0.0), 1.0)  # Ensure in range 0-1
                    elif "Mitigation" in section:
                        current_risk["Mitigation_Plan"] = section.split(":", 1)[1].strip() if ":" in section else section
                        
                    # Check if we have all required fields to consider this risk complete
                    required_fields = ["Risk_ID", "Level", "Project", "Risk_Title", "Risk_Probability"]
                    if all(field in current_risk for field in required_fields):
                        # Calculate risk indices
                        if "Risk_Probability" in current_risk and "Cost_Impact" in current_risk:
                            current_risk["RI_Cost"] = current_risk["Risk_Probability"] * current_risk["Cost_Impact"]
                        
                        if "Risk_Probability" in current_risk and "Time_Impact" in current_risk:
                            current_risk["RI_Time"] = current_risk["Risk_Probability"] * current_risk["Time_Impact"]
                        
                        # Add risk to list and reset current_risk
                        risks.append(current_risk)
                        current_risk = {}
            
            # If we have a partial risk that hasn't been added yet
            if current_risk and "Risk_Title" in current_risk:
                # Set default values for missing fields
                if "Risk_Probability" not in current_risk:
                    current_risk["Risk_Probability"] = 0.5
                if "Cost_Impact" not in current_risk:
                    current_risk["Cost_Impact"] = 100000
                if "Time_Impact" not in current_risk:
                    current_risk["Time_Impact"] = 4
                if "Detection" not in current_risk:
                    current_risk["Detection"] = 0.5
                if "Mitigation_Plan" not in current_risk:
                    current_risk["Mitigation_Plan"] = "To be determined"
                if "Risk_Description" not in current_risk:
                    current_risk["Risk_Description"] = current_risk["Risk_Title"]
                
                # Calculate risk indices
                current_risk["RI_Cost"] = current_risk["Risk_Probability"] * current_risk["Cost_Impact"]
                current_risk["RI_Time"] = current_risk["Risk_Probability"] * current_risk["Time_Impact"]
                
                risks.append(current_risk)
        
        except Exception as e:
            print(f"Error parsing risk response: {e}")
        
        # If we couldn't parse any risks, return mock data
        if not risks:
            risks = self._generate_mock_risks(project_type, project_name, component_name)
        
        return risks
    
    def _generate_mock_risks(self, project_type: str, project_name: str, component_name: str = None) -> List[Dict]:
        """Generate mock risk data when API is not available"""
        target = component_name or project_name
        
        strategic_risks = [
            {
                "Risk_Title": "Market Demand Shift",
                "Risk_Description": f"Significant decline in market demand for {target} due to economic downturn or changing consumer preferences.",
                "Risk_Probability": 0.4,
                "Cost_Impact": 5000000,
                "Time_Impact": 12,
                "Detection": 0.7,
                "Mitigation_Plan": "Implement flexible manufacturing platforms that can quickly adapt to different models; conduct quarterly market analysis to anticipate shifts."
            },
            {
                "Risk_Title": "Regulatory Compliance Failure",
                "Risk_Description": f"Failure to meet new emissions or safety regulations affecting {target}.",
                "Risk_Probability": 0.35,
                "Cost_Impact": 8000000,
                "Time_Impact": 16,
                "Detection": 0.8,
                "Mitigation_Plan": "Establish a dedicated regulatory affairs team for continuous monitoring; build compliance margins into designs."
            },
            {
                "Risk_Title": "Competitive Technology Disruption",
                "Risk_Description": f"Competitors introduce disruptive technology making {target} less competitive.",
                "Risk_Probability": 0.3,
                "Cost_Impact": 10000000,
                "Time_Impact": 24,
                "Detection": 0.5,
                "Mitigation_Plan": "Increase R&D investment; establish technology scouting team; build strategic partnerships with tech companies."
            }
        ]
        
        project_risks = [
            {
                "Risk_Title": "Supply Chain Disruption",
                "Risk_Description": f"Critical component shortage affecting {target} production timeline.",
                "Risk_Probability": 0.45,
                "Cost_Impact": 2000000,
                "Time_Impact": 8,
                "Detection": 0.6,
                "Mitigation_Plan": "Dual-source critical components; increase safety stock levels; develop contingency plans for each tier-1 supplier."
            },
            {
                "Risk_Title": "Quality Control Issues",
                "Risk_Description": f"Unforeseen quality issues discovered during {target} production ramp-up.",
                "Risk_Probability": 0.4,
                "Cost_Impact": 1500000,
                "Time_Impact": 6,
                "Detection": 0.7,
                "Mitigation_Plan": "Implement advanced statistical process control; increase prototype testing; enhance supplier quality management program."
            },
            {
                "Risk_Title": "Resource Allocation Conflicts",
                "Risk_Description": f"Engineering resources diverted from {target} to higher priority projects.",
                "Risk_Probability": 0.5,
                "Cost_Impact": 1000000,
                "Time_Impact": 10,
                "Detection": 0.8,
                "Mitigation_Plan": "Implement formal resource allocation process; establish clear project priorities; develop cross-training program for critical skills."
            }
        ]
        
        operational_risks = [
            {
                "Risk_Title": "Manufacturing Process Variation",
                "Risk_Description": f"Excessive variation in {target} assembly process leading to inconsistent quality.",
                "Risk_Probability": 0.6,
                "Cost_Impact": 800000,
                "Time_Impact": 4,
                "Detection": 0.7,
                "Mitigation_Plan": "Implement Six Sigma process control; increase operator training; install vision systems for real-time inspection."
            },
            {
                "Risk_Title": "Test Equipment Failure",
                "Risk_Description": f"Critical test equipment failure affecting {target} validation timeline.",
                "Risk_Probability": 0.3,
                "Cost_Impact": 500000,
                "Time_Impact": 3,
                "Detection": 0.9,
                "Mitigation_Plan": "Implement preventive maintenance program; maintain backup test equipment; qualify alternative test methods."
            },
            {
                "Risk_Title": "Software Integration Issues",
                "Risk_Description": f"Software integration problems between {target} and vehicle systems.",
                "Risk_Probability": 0.55,
                "Cost_Impact": 1200000,
                "Time_Impact": 6,
                "Detection": 0.6,
                "Mitigation_Plan": "Increase software integration testing earlier in development; improve requirements management; implement continuous integration practices."
            }
        ]
        
        # Select appropriate risks based on project type
        if project_type.lower() == "strategic":
            mock_risks = strategic_risks
        elif project_type.lower() == "project":
            mock_risks = project_risks
        else:  # operational
            mock_risks = operational_risks
        
        # Format the risks with IDs and other required fields
        formatted_risks = []
        for i, risk in enumerate(mock_risks):
            formatted_risk = {
                "Risk_ID": f"R{i+1}",
                "Level": project_type.lower(),
                "Project": target,
                "Owner": "",  # To be filled by user
                "RI_Cost": risk["Risk_Probability"] * risk["Cost_Impact"],
                "RI_Time": risk["Risk_Probability"] * risk["Time_Impact"],
                **risk
            }
            formatted_risks.append(formatted_risk)
        
        return formatted_risks


class RiskEvaluationAgent:
    """Agent responsible for evaluating risks in terms of probability, cost, and time impact"""
    
    def __init__(self, temperature=0.3):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        
        # Initialize OpenAI client
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=temperature,
                api_key=self.openai_api_key
            )
        except Exception as e:
            print(f"Error initializing RiskEvaluationAgent: {e}")
            self.llm = None
    
    def evaluate_risk(self, risk_title: str, risk_description: str, project_type: str, project_name: str) -> Dict:
        """
        Evaluate a risk in terms of probability, cost impact, and time impact
        
        Args:
            risk_title: Title of the risk
            risk_description: Description of the risk
            project_type: Type of project (strategic, project, operational)
            project_name: Name of the project
            
        Returns:
            Dictionary with probability, cost impact, time impact, and detection values
        """
        if not self.llm:
            # Return some reasonable defaults if OpenAI is not available
            return {
                "Risk_Probability": round(random.uniform(0.2, 0.7), 2),
                "Cost_Impact": random.randint(300000, 3000000),
                "Time_Impact": random.randint(2, 20),
                "Detection": round(random.uniform(0.3, 0.8), 2)
            }
        
        # Prepare the prompt
        system_prompt = f"""You are an expert in automotive risk assessment. 
        Evaluate the following risk for the {project_type} level project "{project_name}":
        
        Risk Title: {risk_title}
        Risk Description: {risk_description}
        
        Provide a precise evaluation of:
        1. Risk Probability (0.0-1.0) - How likely is this risk to occur?
        2. Cost Impact (in Euros €) - What would be the financial impact if this risk occurs?
        3. Time Impact (in weeks) - How much schedule delay would this risk cause?
        4. Detection (0.0-1.0) - How easy is it to detect this risk before it fully impacts? (0 = very hard to detect, 1 = very easy to detect)
        
        Return only the numeric values in a structured format."""
        
        try:
            # Generate response
            result = self.llm.invoke(system_prompt)
            
            # Parse the response
            evaluation = self._parse_evaluation_response(result.content)
            return evaluation
            
        except Exception as e:
            print(f"Error in risk evaluation: {e}")
            # Fallback to random values if the API call fails
            return {
                "Risk_Probability": round(random.uniform(0.2, 0.7), 2),
                "Cost_Impact": random.randint(300000, 3000000),
                "Time_Impact": random.randint(2, 20),
                "Detection": round(random.uniform(0.3, 0.8), 2)
            }
    
    def _parse_evaluation_response(self, response: str) -> Dict:
        """Parse the LLM response into structured evaluation data"""
        evaluation = {
            "Risk_Probability": 0.5,
            "Cost_Impact": 1000000,
            "Time_Impact": 8,
            "Detection": 0.6
        }
        
        try:
            # Extract probability
            if "Probability" in response:
                prob_line = next((line for line in response.split('\n') if "Probability" in line), "")
                prob_value = next((float(s) for s in prob_line.split() if s.replace('.', '', 1).isdigit()), 0.5)
                evaluation["Risk_Probability"] = min(max(prob_value, 0.0), 1.0)  # Ensure in range 0-1
            
            # Extract cost impact
            if "Cost Impact" in response or "Financial Impact" in response:
                cost_line = next((line for line in response.split('\n') if "Cost Impact" in line or "Financial Impact" in line or "€" in line), "")
                # Extract digits from cost line
                cost_digits = ''.join(filter(lambda x: x.isdigit(), cost_line))
                if cost_digits:
                    evaluation["Cost_Impact"] = int(cost_digits)
            
            # Extract time impact
            if "Time Impact" in response or "Schedule" in response:
                time_line = next((line for line in response.split('\n') if "Time Impact" in line or "Schedule" in line or "weeks" in line), "")
                time_value = next((int(s) for s in time_line.split() if s.isdigit()), 8)
                evaluation["Time_Impact"] = time_value
            
            # Extract detection
            if "Detection" in response:
                det_line = next((line for line in response.split('\n') if "Detection" in line), "")
                det_value = next((float(s) for s in det_line.split() if s.replace('.', '', 1).isdigit()), 0.6)
                evaluation["Detection"] = min(max(det_value, 0.0), 1.0)  # Ensure in range 0-1
                
        except Exception as e:
            print(f"Error parsing evaluation response: {e}")
        
        return evaluation


class MitigationPlanAgent:
    """Agent responsible for creating mitigation plans for identified risks"""
    
    def __init__(self, temperature=0.6):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.temperature = temperature
        
        # Initialize OpenAI client
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                temperature=temperature,
                api_key=self.openai_api_key
            )
        except Exception as e:
            print(f"Error initializing MitigationPlanAgent: {e}")
            self.llm = None
    
    def create_mitigation_plan(self, risk_title: str, risk_description: str, 
                              project_type: str, project_name: str, 
                              probability: float, cost_impact: float, 
                              time_impact: float) -> str:
        """
        Create a mitigation plan for an identified risk
        
        Args:
            risk_title: Title of the risk
            risk_description: Description of the risk
            project_type: Type of project (strategic, project, operational)
            project_name: Name of the project
            probability: Risk probability
            cost_impact: Cost impact
            time_impact: Time impact
            
        Returns:
            Mitigation plan as a string
        """
        if not self.llm:
            # Return some default mitigation plans if OpenAI is not available
            return self._get_default_mitigation_plan(risk_title, project_type)
        
        # Prepare the prompt
        system_prompt = f"""You are an expert in automotive risk mitigation. 
        Create a detailed mitigation plan for the following risk:
        
        Risk Title: {risk_title}
        Risk Description: {risk_description}
        Project Type: {project_type}
        Project: {project_name}
        Risk Probability: {probability}
        Cost Impact: €{cost_impact:,.2f}
        Time Impact: {time_impact} weeks
        
        Your mitigation plan should:
        1. Identify specific actions to reduce probability
        2. Identify specific actions to reduce impact
        3. Define clear responsibilities
        4. Include contingency planning
        5. Be realistic and implementable in the automotive industry
        
        Keep the plan concise but comprehensive."""
        
        try:
            # Generate response
            result = self.llm.invoke(system_prompt)
            return result.content
            
        except Exception as e:
            print(f"Error in mitigation planning: {e}")
            # Fallback to default mitigation plans if the API call fails
            return self._get_default_mitigation_plan(risk_title, project_type)
    
    def _get_default_mitigation_plan(self, risk_title: str, project_type: str) -> str:
        """Get a default mitigation plan based on risk title and project type"""
        
        if "supply chain" in risk_title.lower():
            return "1. Identify and qualify secondary suppliers for critical components. 2. Implement a supplier risk monitoring system. 3. Increase safety stock for high-risk components. 4. Develop contingency production plans for critical component shortages. 5. Conduct quarterly supply chain risk reviews with cross-functional team."
        
        elif "quality" in risk_title.lower():
            return "1. Increase frequency of quality audits during development. 2. Implement advanced statistical process control. 3. Conduct FMEA (Failure Mode and Effects Analysis) workshops with suppliers. 4. Create rapid response quality teams ready to address issues. 5. Enhance pre-production testing protocols and acceptance criteria."
        
        elif "regulatory" in risk_title.lower():
            return "1. Establish dedicated regulatory affairs team tracking upcoming regulations. 2. Implement monthly compliance reviews throughout development. 3. Build compliance margin into product specifications. 4. Develop relationships with regulatory bodies. 5. Create contingency plans for potential regulatory changes."
        
        elif "technology" in risk_title.lower() or "software" in risk_title.lower():
            return "1. Increase early-stage technology validation and testing. 2. Implement agile development methodologies with frequent integration testing. 3. Create technology contingency roadmaps. 4. Establish partnerships with technology specialists. 5. Define clear fallback technologies that meet minimum requirements."
        
        elif "market" in risk_title.lower() or "demand" in risk_title.lower():
            return "1. Develop flexible production planning to adjust to market changes. 2. Implement quarterly market analysis and forecast reviews. 3. Create modular product architectures that can be rapidly adapted. 4. Develop contingency plans for different market scenarios. 5. Establish early warning indicators for market shifts."
        
        elif "resource" in risk_title.lower():
            return "1. Implement formal resource allocation process with executive oversight. 2. Create cross-training program for critical skills. 3. Develop contractor network for surge capacity. 4. Implement weekly resource tracking and forecasting. 5. Establish clear escalation path for resource conflicts."
        
        elif "test" in risk_title.lower() or "validation" in risk_title.lower():
            return "1. Create redundancy for critical test equipment. 2. Implement preventive maintenance program for test systems. 3. Qualify alternative test methods as backup. 4. Develop agreements with external test facilities. 5. Create contingency test plans with reduced scope for emergencies."
        
        # Default generic plan
        if project_type.lower() == "strategic":
            return "1. Establish executive steering committee for risk oversight. 2. Develop alternative strategic scenarios and plans. 3. Implement quarterly risk review process. 4. Create cross-functional response teams. 5. Develop detailed contingency plans for major risk categories."
        
        elif project_type.lower() == "project":
            return "1. Implement formal risk management process with weekly reviews. 2. Create focused mitigation plans for top 5 risks. 3. Assign risk owners with clear responsibilities. 4. Establish contingency budget and schedule buffers. 5. Develop escalation procedures for emerging risks."
        
        else:  # operational
            return "1. Implement daily monitoring of key risk indicators. 2. Create standardized troubleshooting procedures. 3. Establish backup operational processes. 4. Train team on risk identification and escalation. 5. Conduct regular operational risk simulations."


class AgentCoordinator:
    """Coordinates multiple agents for the risk assessment process"""
    
    def __init__(self):
        # Load configuration if available
        self.config = self._load_config()
        
        # Initialize agents with temperature from config
        self.web_search_agent = WebSearchAgent(
            temperature=self.config.get("web_search_agent", {}).get("temperature", 0.7)
        )
        
        self.risk_evaluation_agent = RiskEvaluationAgent(
            temperature=self.config.get("risk_evaluation_agent", {}).get("temperature", 0.3)
        )
        
        self.mitigation_agent = MitigationPlanAgent(
            temperature=self.config.get("mitigation_agent", {}).get("temperature", 0.6)
        )
    
    def _load_config(self) -> Dict:
        """Load agent configuration from file"""
        try:
            config_path = Path("config/agent_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
            
            # Default configuration if file doesn't exist
            return {
                "web_search_agent": {"enabled": True, "temperature": 0.7},
                "risk_evaluation_agent": {"enabled": True, "temperature": 0.3},
                "mitigation_agent": {"enabled": True, "temperature": 0.6}
            }
        except Exception as e:
            print(f"Error loading configuration: {e}")
            # Return default configuration on error
            return {
                "web_search_agent": {"enabled": True, "temperature": 0.7},
                "risk_evaluation_agent": {"enabled": True, "temperature": 0.3},
                "mitigation_agent": {"enabled": True, "temperature": 0.6}
            }
    
    def generate_risk_assessment(self, initial_data: Dict) -> List[Dict]:
        """
        Generate a risk assessment using the agent team
        
        Args:
            initial_data: Initial data with product range, projects, and components
            
        Returns:
            List of dictionaries containing risk information
        """
        all_risks = []
        
        # Process each level of the hierarchy
        
        # 1. Strategic level - Process each product range
        for product_range in initial_data.get("product_range", []):
            range_name = product_range.get("name", "Unknown Range")
            
            # Get risks for the product range (strategic level)
            if self.config.get("web_search_agent", {}).get("enabled", True):
                strategic_risks = self.web_search_agent.search_risks(
                    project_type="strategic",
                    project_name=range_name
                )
                
                all_risks.extend(strategic_risks)
            
            # 2. Project level - Process each project in the range
            for project in product_range.get("projects", []):
                project_name = project.get("name", "Unknown Project")
                
                # Get risks for the project (project level)
                if self.config.get("web_search_agent", {}).get("enabled", True):
                    project_risks = self.web_search_agent.search_risks(
                        project_type="project",
                        project_name=project_name
                    )
                    
                    all_risks.extend(project_risks)
                
                # 3. Operational level - Process each component in the project
                for component in project.get("components", []):
                    component_name = component.get("name", "Unknown Component")
                    
                    # Get risks for the component (operational level)
                    if self.config.get("web_search_agent", {}).get("enabled", True):
                        component_risks = self.web_search_agent.search_risks(
                            project_type="operational",
                            project_name=project_name,
                            component_name=component_name
                        )
                        
                        all_risks.extend(component_risks)
        
        # For each risk, enhance it with the risk evaluation agent if enabled
        if self.config.get("risk_evaluation_agent", {}).get("enabled", True):
            for risk in all_risks:
                # Skip if already has complete evaluation
                if all(key in risk for key in ["Risk_Probability", "Cost_Impact", "Time_Impact", "Detection"]):
                    continue
                
                # Get evaluation
                evaluation = self.risk_evaluation_agent.evaluate_risk(
                    risk_title=risk.get("Risk_Title", ""),
                    risk_description=risk.get("Risk_Description", ""),
                    project_type=risk.get("Level", ""),
                    project_name=risk.get("Project", "")
                )
                
                # Update risk with evaluation
                risk.update(evaluation)
                
                # Calculate risk indices
                risk["RI_Cost"] = risk["Risk_Probability"] * risk["Cost_Impact"]
                risk["RI_Time"] = risk["Risk_Probability"] * risk["Time_Impact"]
        
        # For each risk, enhance it with mitigation plan if enabled
        if self.config.get("mitigation_agent", {}).get("enabled", True):
            for risk in all_risks:
                # Skip if already has mitigation plan
                if "Mitigation_Plan" in risk and risk["Mitigation_Plan"]:
                    continue
                
                # Get mitigation plan
                mitigation_plan = self.mitigation_agent.create_mitigation_plan(
                    risk_title=risk.get("Risk_Title", ""),
                    risk_description=risk.get("Risk_Description", ""),
                    project_type=risk.get("Level", ""),
                    project_name=risk.get("Project", ""),
                    probability=risk.get("Risk_Probability", 0.5),
                    cost_impact=risk.get("Cost_Impact", 1000000),
                    time_impact=risk.get("Time_Impact", 4)
                )
                
                # Update risk with mitigation plan
                risk["Mitigation_Plan"] = mitigation_plan
        
        return all_risks
        
    def update_risk_evaluation(self, risk: Dict) -> Dict:
        """Update the evaluation of a single risk"""
        if not self.config.get("risk_evaluation_agent", {}).get("enabled", True):
            return risk
        
        evaluation = self.risk_evaluation_agent.evaluate_risk(
            risk_title=risk.get("Risk_Title", ""),
            risk_description=risk.get("Risk_Description", ""),
            project_type=risk.get("Level", ""),
            project_name=risk.get("Project", "")
        )
        
        # Update risk with evaluation
        risk.update(evaluation)
        
        # Calculate risk indices
        risk["RI_Cost"] = risk["Risk_Probability"] * risk["Cost_Impact"]
        risk["RI_Time"] = risk["Risk_Probability"] * risk["Time_Impact"]
        
        return risk
    
    def update_mitigation_plan(self, risk: Dict) -> Dict:
        """Update the mitigation plan for a single risk"""
        if not self.config.get("mitigation_agent", {}).get("enabled", True):
            return risk
        
        mitigation_plan = self.mitigation_agent.create_mitigation_plan(
            risk_title=risk.get("Risk_Title", ""),
            risk_description=risk.get("Risk_Description", ""),
            project_type=risk.get("Level", ""),
            project_name=risk.get("Project", ""),
            probability=risk.get("Risk_Probability", 0.5),
            cost_impact=risk.get("Cost_Impact", 1000000),
            time_impact=risk.get("Time_Impact", 4)
        )
        
        # Update risk with mitigation plan
        risk["Mitigation_Plan"] = mitigation_plan
        
        return risk 