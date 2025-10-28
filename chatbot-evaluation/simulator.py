# simulator.py
import random
import yaml
import database

class Simulator:
    KEYWORD_MAP = {
        "TRACK": ["track", "where", "status"],
        "LATE": ["late", "delayed"],
        "MISS": ["missing", "didn't get", "did not get"],
        "WRONG": ["wrong", "not what i ordered"],
        "PAYMENT": ["payment", "charge", "billing"],
        "ADDRESS": ["address"],
        "COLD": ["cold", "not hot"],
        "QUALITY": ["bad", "stale", "quality"],
    }
    def __init__(self, templates_file='scenarios.yaml'):
        try:
            with open(templates_file, 'r') as file:
                self.scenario_templates = yaml.safe_load(file)
            print(f"[Simulator] Successfully loaded {len(self.scenario_templates)} scenario templates from {templates_file}.")
        except FileNotFoundError:
            print(f"FATAL ERROR: The scenarios file '{templates_file}' was not found.")
            raise
        except Exception as e:
            print(f"FATAL ERROR: Could not parse scenario templates. Check YAML formatting. Details: {e}")
            raise

    def _generate_order_id(self) -> str:
        """Generates a random, formatted order ID."""
        return f"ORD-{random.randint(100000, 999999)}"

    def assign_and_create_order(self, user_input: str = None, label: str = None) -> tuple[str, str]:
        """
        Determines the appropriate scenario label and creates a corresponding order in the database.
        
        Priority:
        1.  Uses the provided `label` if available.
        2.  Otherwise, infers the label from `user_input` keywords.
        3.  Falls back to a default if no match is found.
        """
        # Determine the scenario label using the keyword map (ordered for priority).
        if not label and user_input:
            # If no label is provided, infer it from user input keywords using KEYWORD_MAP.
            inp_lower = user_input.lower()
            for lbl, keywords in self.KEYWORD_MAP.items():
                if any(kw in inp_lower for kw in keywords):
                    label = lbl
                    break

        # If no label was provided and no keywords matched, or if no input was given at all.
        if not label:
            label = next(iter(self.scenario_templates), "QUALITY")  # A safe default scenario.
        
        # Now, create the order using the determined label.
        new_order_id = self._generate_order_id()
        template = self.scenario_templates.get(label)

        if not template:
            print(f"WARNING: No template found in scenarios.yaml for label '{label}'. Creating an empty order.")
            template = {} # Prevent a crash by providing an empty dict.

        database.create_order(new_order_id, label, template)
        
        print(f"\n[Simulator]: New order {new_order_id} created in DB for scenario '{label}'.")
        return new_order_id, label
