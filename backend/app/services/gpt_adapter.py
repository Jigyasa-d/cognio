def generate_adaptation(prediction):
    level = prediction.get("strain_level")

    if level == "HIGH":
        return "You seem to be struggling. Try reviewing basics or take a short break."

    elif level == "MODERATE":
        return "You are doing okay. Consider slowing down and revisiting difficult concepts."

    else:
        return "Great progress! Keep going at this pace."