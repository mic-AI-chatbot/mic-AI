import re
from typing import Dict, Any, Callable, Tuple, List
from .conversation import ConversationManager
from tools.base_tool import BaseTool

class IntentDispatcher:
    """
    Dispatches user input to the appropriate tool based on detected intent.
    """

    def __init__(self, tools: Dict[str, Callable]):
        """
        Initializes the IntentDispatcher.

        Args:
            tools: A dictionary mapping intent names to tool functions.
        """
        self.tools = tools
        self.intent_keywords = self._create_intent_keywords()

    def _create_intent_keywords(self) -> Dict[str, str]:
        """
        Creates a mapping from keywords to intents.
        """
        return {
            "web search:": "web_search",
            "generate code:": "generate_code",
            "explain code:": "explain_code",
            "refactor code:": "refactor_code",
            "generate image:": "generate_image",
            "analyze image:": "analyze_image",
            "write poem about:": "write_poem",
            "write story about:": "write_story",
            "write song about:": "write_song",
            "write essay about:": "write_essay",
            "write article about:": "write_article",
            "analyze data:": "analyze_data",
            "read file:": "read_file",
            "summarize:": "summarize",
            "generate text:": "generate_text",
            "clone voice:": "clone_voice",
            "generate chart:": "generate_chart",
            "format code:": "format_code",
            "manage dependency:": "manage_dependency",
            "generate api docs:": "generate_api_docs",
            "migrate database:": "migrate_database",
            "analyze log:": "analyze_log",
            "monitor performance:": "monitor_performance",
            "scan for vulnerabilities:": "scan_for_vulnerabilities",
            "analyze code complexity:": "analyze_code_complexity",
            "manage feature flag:": "manage_feature_flag",
            "orchestrate a/b test:": "orchestrate_a_b_test",
            "collect user feedback:": "collect_user_feedback",
            "generate report:": "generate_report",
            "anonymize data:": "anonymize_data",
            "start collaboration:": "start_collaboration",
            "manage code snippet:": "manage_code_snippet",
            "manage env var:": "manage_env_var",
            "orchestrate container:": "orchestrate_container",
            "provision cloud resource:": "provision_cloud_resource",
            "analyze network traffic:": "analyze_network_traffic",
            "check system health:": "check_system_health",
            "deploy application:": "deploy_application",
            "assist version control:": "assist_version_control",
            "integrate issue tracker:": "integrate_issue_tracker",
            "generate meeting minutes:": "generate_meeting_minutes",
            "create presentation:": "create_presentation",
            "automate spreadsheet:": "automate_spreadsheet",
            "edit pdf:": "edit_pdf",
            "resize image:": "resize_image",
            "edit audio:": "edit_audio",
            "convert video:": "convert_video",
            "compress file:": "compress_file",
            "manage clipboard:": "manage_clipboard",
            "annotate screenshot:": "annotate_screenshot",
            "convert unit:": "convert_unit",
            "convert timezone:": "convert_timezone",
            "generate recipe:": "generate_recipe",
            "plan workout:": "plan_workout",
            "create study schedule:": "create_study_schedule",
            "track finance:": "track_finance",
            "plan travel:": "plan_travel",
            "api test:": "api_test",
            "calendar:": "calendar",
            "debug code:": "debug_code",
            "review code:": "review_code",
            "query db:": "query_db",
            "create doc:": "create_doc",
            "send email:": "send_email",
            "extract entities:": "extract_entities",
            "search kb:": "search_kb",
            "generate music:": "generate_music",
            "net diag:": "net_diag",
            "generate password:": "generate_password",
            "scaffold project:": "scaffold_project",
            "analyze sentiment:": "analyze_sentiment",
            "transcribe:": "transcribe",
            "system monitor:": "system_monitor",
            "translate:": "translate",
            "generate unit test:": "generate_unit_test",
            "process video:": "process_video",
            "scrape_web:": "scrape_web",
            "cross_lingual_information_retrieval:": "cross_lingual_information_retrieval",
            "nuanced_sentiment_analysis:": "nuanced_sentiment_analysis",
            "stylometric_analysis:": "stylometric_analysis",
            "figurative_language_interpreter:": "figurative_language_interpreter",
            "dialogue_state_tracker:": "dialogue_state_tracker",
            "long_form_abstractive_summarization:": "long_form_abstractive_summarization",
            "narrative_generation:": "narrative_generation",
            "code_documentation_generator:": "code_documentation_generator",
            "legal_document_analyzer:": "legal_document_analyzer",
            "medical_text_deidentifier:": "medical_text_deidentifier",
            "argument_miner:": "argument_miner",
            "complex_question_answering:": "complex_question_answering",
            "fact_checker:": "fact_checker",
            "personalized_content_generator:": "personalized_content_generator",
            "speech_to_text_with_diarization:": "speech_to_text_with_diarization",
            "emotional_text_to_speech:": "emotional_text_to_speech",
            "domain_specific_language_model_finetuning:": "domain_specific_language_model_finetuning",
            "advanced_grammar_and_style_correction:": "advanced_grammar_and_style_correction",
            "structured_data_to_text_report_writer:": "structured_data_to_text_report_writer",
            "chatbot_personality_generator:": "chatbot_personality_generator",
            "semantic_search:": "semantic_search",
            "discourse_analyzer:": "discourse_analyzer",
            "context_aware_translation:": "context_aware_translation",
            "text_paraphraser_and_rewriter:": "text_paraphraser_and_rewriter",
            "automated_essay_scorer:": "automated_essay_scorer",
            "generative_image_synthesis:": "generative_image_synthesis",
            "image_inpainting_outpainting:": "image_inpainting_outpainting",
            "style_transfer:": "style_transfer",
            "super_resolution:": "super_resolution",
            "3d_reconstruction_from_2d:": "3d_reconstruction_from_2d",
            "human_pose_estimation:": "human_pose_estimation",
            "action_recognition:": "action_recognition",
            "gaze_tracking:": "gaze_tracking",
            "facial_landmark_detection:": "facial_landmark_detection",
            "image_captioning:": "image_captioning",
            "video_summarization:": "video_summarization",
            "anomaly_detection_in_surveillance:": "anomaly_detection_in_surveillance",
            "medical_image_segmentation:": "medical_image_segmentation",
            "defect_detection_in_manufacturing:": "defect_detection_in_manufacturing",
            "crowd_counting:": "crowd_counting",
            "augmented_reality_content_generation:": "augmented_reality_content_generation",
            "virtual_try_on:": "virtual_try_on",
            "image_forgery_detection:": "image_forgery_detection",
            "object_tracking_in_dynamic_environments:": "object_tracking_in_dynamic_environments",
            "visual_question_answering:": "visual_question_answering",
            "automated_theorem_proving:": "automated_theorem_proving",
            "strategic_game_playing:": "strategic_game_playing",
            "automated_scheduling_and_optimization:": "automated_scheduling_and_optimization",
            "causal_inference:": "causal_inference",
            "hypothesis_generation:": "hypothesis_generation",
            "automated_experiment_design:": "automated_experiment_design",
            "knowledge_graph_construction:": "knowledge_graph_construction",
            "multi_agent_system_coordination:": "multi_agent_system_coordination",
            "robotic_path_planning:": "robotic_path_planning",
            "automated_debugging:": "automated_debugging",
            "legal_case_prediction:": "legal_case_prediction",
            "financial_market_prediction:": "financial_market_prediction",
            "drug_discovery_and_molecular_design:": "drug_discovery_and_molecular_design",
            "supply_chain_resilience_planning:": "supply_chain_resilience_planning",
            "personalized_education_path_planning:": "personalized_education_path_planning",
            "resource_allocation_optimization:": "resource_allocation_optimization",
            "automated_negotiation:": "automated_negotiation",
            "ethical_decision_making_frameworks:": "ethical_decision_making_frameworks",
            "counterfactual_reasoning:": "counterfactual_reasoning",
            "automated_policy_generation:": "automated_policy_generation",
            "music_composition:": "music_composition",
            "sound_design_and_synthesis:": "sound_design_and_synthesis",
            "video_generation:": "video_generation",
            "game_level_design:": "game_level_design",
            "fashion_design:": "fashion_design",
            "architectural_design:": "architectural_design",
            "recipe_generation:": "recipe_generation",
            "poetry_generation:": "poetry_generation",
            "choreography_generation:": "choreography_generation",
            "3d_model_generation:": "3d_model_generation",
            "meta_learning:": "meta_learning",
            "continual_learning:": "continual_learning",
            "few_shot_learning:": "few_shot_learning",
            "self_supervised_learning:": "self_supervised_learning",
            "reinforcement_learning_from_human_feedback:": "reinforcement_learning_from_human_feedback",
            "active_learning:": "active_learning",
            "transfer_learning:": "transfer_learning",
            "adaptive_control_systems:": "adaptive_control_systems",
            "personalized_learning_agents:": "personalized_learning_agents",
            "curriculum_learning:": "curriculum_learning",
            "emotion_aware_interaction:": "emotion_aware_interaction",
            "gesture_recognition_and_interpretation:": "gesture_recognition_and_interpretation",
            "brain_computer_interface_interpretation:": "brain_computer_interface_interpretation",
            "haptic_feedback_generation:": "haptic_feedback_generation",
            "social_robotics:": "social_robotics",
            "human_robot_collaboration:": "human_robot_collaboration",
            "personalized_digital_avatars:": "personalized_digital_avatars",
            "context_aware_assistants:": "context_aware_assistants",
            "proactive_assistance:": "proactive_assistance",
            "adaptive_user_interfaces:": "adaptive_user_interfaces",
            "climate_modeling_and_prediction:": "climate_modeling_and_prediction",
            "astrophysics_data_analysis:": "astrophysics_data_analysis",
            "materials_science_discovery:": "materials_science_discovery",
            "genomic_data_analysis_and_drug_repurposing:": "genomic_data_analysis_and_drug_repurposing",
            "agricultural_yield_prediction_and_optimization:": "agricultural_yield_prediction_and_optimization",
            "urban_planning_and_smart_city_optimization:": "urban_planning_and_smart_city_optimization",
            "disaster_response_and_management:": "disaster_response_and_management",
            "archaeological_site_analysis:": "archaeological_site_analysis",
            "forensic_analysis:": "forensic_analysis",
            "sports_analytics_and_performance_optimization:": "sports_analytics_and_performance_optimization",
            "legal_research_and_document_review:": "legal_research_and_document_review",
            "environmental_monitoring_and_pollution_tracking:": "environmental_monitoring_and_pollution_tracking",
            "personalized_healthcare_and_treatment_plans:": "personalized_healthcare_and_treatment_plans",
            "financial_risk_assessment:": "financial_risk_assessment",
            "insurance_underwriting_automation:": "insurance_underwriting_automation",
            "geological_survey_and_resource_exploration:": "geological_survey_and_resource_exploration",
            "educational_content_curation:": "educational_content_curation",
            "art_restoration_and_preservation:": "art_restoration_and_preservation",
            "wildlife_monitoring_and_conservation:": "wildlife_monitoring_and_conservation",
            "cybersecurity_threat_hunting:": "cybersecurity_threat_hunting",
            "synthetic_data_generation:": "synthetic_data_generation",
            "data_augmentation_for_low_resource_scenarios:": "data_augmentation_for_low_resource_scenarios",
            "missing_data_imputation:": "missing_data_imputation",
            "data_denoising_and_cleaning:": "data_denoising_and_cleaning",
            "data_anonymization:": "data_anonymization",
            "bias_detection_and_mitigation:": "bias_detection_and_mitigation",
            "fairness_aware_ai_development:": "fairness_aware_ai_development",
            "privacy_preserving_ai_training:": "privacy_preserving_ai_training",
            "accountability_frameworks_for_ai:": "accountability_frameworks_for_ai",
            "transparency_in_ai_decision_making:": "transparency_in_ai_decision_making",
            "ai_governance_and_policy_enforcement:": "ai_governance_and_policy_enforcement",
            "human_in_the_loop_optimization:": "human_in_the_loop_optimization",
            "robustness_testing:": "robustness_testing",
            "ai_safety_and_alignment_research:": "ai_safety_and_alignment_research",
            "explainable_ai_for_non_experts:": "explainable_ai_for_non_experts",

            # Placeholder tools
            "schedule meeting:": "schedule_meeting",
            "plan travel:": "plan_travel",
            "monitor health:": "monitor_health",
            "generate storyboard:": "generate_storyboard",
            "design logo:": "design_logo",
            "design interior:": "design_interior",
            "generate tutorial:": "generate_tutorial",
            "tutor language:": "tutor_language",
            "solve math problem:": "solve_math_problem",
            "start game:": "start_game",
            "tell joke:": "tell_joke",
            "recommend movie:": "recommend_movie",

            # Futuristic tools
            "build cognitive model:": "build_cognitive_model",
            "generate learning curriculum:": "generate_learning_curriculum",
            "detect cognitive bias:": "detect_cognitive_bias",
            "analyze dream journal:": "analyze_dream_journal",
            "create digital twin:": "create_digital_twin",
            "simulate economic system:": "simulate_economic_system",
            "simulate history:": "simulate_history",
            "build metaverse:": "build_metaverse",
            "discover science:": "discover_science",
            "simulate nanotechnology:": "simulate_nanotechnology",
            "design quantum algorithm:": "design_quantum_algorithm",
            "simulate climate engineering:": "simulate_climate_engineering",
            "assist film director:": "assist_film_director",
            "create interactive narrative:": "create_interactive_narrative",
            "collaborate on art:": "collaborate_on_art",
            "compose emotional music:": "compose_emotional_music",
        }

    def detect_intent(self, user_input: str) -> Tuple[str, str]:
        """
        Detects the user's intent and extracts the argument string.
        """
        user_input_lower = user_input.lower()
        
        matched_intents = []
        for keyword, intent in self.intent_keywords.items():
            if user_input_lower.startswith(keyword):
                matched_intents.append((keyword, intent))

        if len(matched_intents) == 1:
            keyword, intent = matched_intents[0]
            args_str = user_input[len(keyword):].strip()
            return intent, args_str
        elif len(matched_intents) > 1:
            # Handle ambiguity by choosing the longest matching keyword
            longest_keyword = ""
            best_intent = ""
            for keyword, intent in matched_intents:
                if len(keyword) > len(longest_keyword):
                    longest_keyword = keyword
                    best_intent = intent
            
            args_str = user_input[len(longest_keyword):].strip()
            return best_intent, args_str

        # If no keyword matches, check for simple ambiguous words
        if user_input_lower in ["generate", "create", "make"]:
            return "ambiguous_generate", ""

        return "conversational_ai", user_input # Default intent

    def detect_chained_intents(self, user_input: str) -> List[Tuple[str, str]]:
        """
        Detects a chain of intents separated by 'and then'.
        """
        # Use regex to split to handle casing
        parts = re.split(r'\s+and then\s+', user_input, flags=re.IGNORECASE)
        intents = []
        for part in parts:
            intent, args_str = self.detect_intent(part.strip())
            intents.append((intent, args_str))
        return intents

    def _parse_args(self, args_str: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Parses the argument string into positional and keyword arguments.
        """
        kwargs = {}
        # Regex to find key-value pairs, handling quoted strings
        kv_pair_regex = r"""(\w+)\s*=\s*("[^"]*"|'[^']*'|\S+)"""
        
        matches = re.findall(kv_pair_regex, args_str)
        for key, value in matches:
            # Remove quotes from the value if they exist
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith(''') and value.endswith(''')):
                kwargs[key] = value[1:-1]
            else:
                try:
                    # Try to convert to a number if possible
                    kwargs[key] = int(value)
                except ValueError:
                    try:
                        kwargs[key] = float(value)
                    except ValueError:
                        kwargs[key] = value

        # The remaining parts of the string are positional arguments
        # Remove the matched key-value pairs to find positional args
        processed_args_str = re.sub(kv_pair_regex, '', args_str).strip()
        args = [arg.strip() for arg in processed_args_str.split() if arg.strip()]

        return args, kwargs

    def dispatch(self, conversation: ConversationManager, intent: str, args_str: str) -> str:
        """
        Dispatches the user's request to the appropriate tool.
        """
        if intent in self.tools:
            tool_instance = self.tools[intent] # tool_instance is now a BaseTool instance

            if not isinstance(tool_instance, BaseTool):
                return f"Error: Tool '{intent}' is not a valid BaseTool instance."

            try:
                # The conversational_ai tool is special, it takes the whole history
                if intent == "conversational_ai":
                    # Assuming conversational_ai tool has an execute method that takes history
                    return tool_instance.execute(history=conversation.history)

                args, kwargs = self._parse_args(args_str)
                
                # For code generation tool, we need to pass the command as the first argument
                # This logic might need to be moved into the tool itself for better encapsulation
                if intent in ["generate_code", "explain_code", "refactor_code", "generate_unit_test"]:
                    kwargs['command'] = intent

                # If there are positional args, and the tool expects a single query string,
                # then join the positional args to form the query.
                # This is a heuristic and might need to be improved.
                if args and not kwargs:
                     query = " ".join(args)
                     return tool_instance.execute(query=query) # Assuming execute takes a query argument
                
                return tool_instance.execute(*args, **kwargs)
            except Exception as e:
                return f"Error calling tool {intent}: {e}"
        else:
            return "I'm sorry, I don't understand that."