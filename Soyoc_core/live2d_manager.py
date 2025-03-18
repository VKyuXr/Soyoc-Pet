import live2d.v3 as live2d
import os, json, logging
import Soyoc_core.physics as Soyoc_physics
import Soyoc_core.motion_manager as Soyoc_motion_manager

class Live2DPhysics:
    def __init__(self, model: live2d.LAppModel, model_params: dict, model_params_range: dict, physics_setting_count: int, physics_dictionary: list[dict]):
        self.model = model
        self.model_params = model_params.copy()
        self.model_params_range = model_params_range
        self.physics_setting_count = physics_setting_count
        self.physics_settings: list[Soyoc_physics.PhysicsSetting] = []
        for item in physics_dictionary:
            physics_setting = Soyoc_physics.PhysicsSetting(item["Id"], item["Name"])
            self.physics_settings.append(physics_setting)
    
    def set_physics_settings(self, physics_setting_params: list[dict]):
        if len(physics_setting_params) is not self.physics_setting_count:
            logging.error("PhysicsSettings 长度与 PhysicsSettingCount 不符，请检查 .physics3.json 文件")
            return

        for index, physics_setting_param in enumerate(physics_setting_params):
            if physics_setting_param["Id"] == self.physics_settings[index].get_id():
                self.physics_settings[index].add_input_param(physics_setting_param["Input"])
                self.physics_settings[index].add_output_param(physics_setting_param["Output"])
                self.physics_settings[index].add_physics_simulator(
                    count=len(physics_setting_param["Vertices"]),
                    mobility=[item["Mobility"] for item in physics_setting_param["Vertices"]],
                    delay=[item["Delay"] for item in physics_setting_param["Vertices"]],
                    acceleration=[item["Acceleration"] for item in physics_setting_param["Vertices"]],
                    radius=[item["Radius"] for item in physics_setting_param["Vertices"]])
            else:
                logging.warning("PhysicsSettings 顺序与 PhysicsDictionary 不一致，请检查 .physics3.json 文件")
    
    def update_model_params(self, new_model_params: dict, delta_t: float, velocity: list):
        model_params_normalized = {}
        for key in new_model_params:
            model_params_normalized[key] = new_model_params[key] * 20 / (self.model_params_range[key]["max"] - self.model_params_range[key]["min"])

        output_delta_all = {}
        for physics_setting in self.physics_settings:
            physics_setting.inertial_simulation(velocity, delta_t)
            output_delta = physics_setting.calculate_output_delta(new_model_params, delta_t)

            for key in output_delta:
                output_delta[key] = output_delta[key] * (self.model_params_range[key]["max"] - self.model_params_range[key]["min"]) / 20
            output_delta_all.update(output_delta)

        self.model_params.update(new_model_params)
        self.model_params.update(output_delta_all)

        return self.model_params

class Live2DManager:
    def __init__(self, config_editor):
        self.config_editor = config_editor
        self.l2d_folder_name = self.config_editor.l2d_model
        self.model: live2d.LAppModel
        self.model_params: dict = {}
        self.model_params_range: dict = {}
        self.l2d_physics: Live2DPhysics
        self.velocity = [0, 0]
        self.state = {
            "track": True,
            "music": False,
            "motion": False,
        }
        self.motion_now: str
        self.motion_manager = Soyoc_motion_manager.MotionManager(self.config_editor)
        self.to_default = 0
    
    def is_track(self):
        return self.state["track"]
    
    def is_music(self):
        return self.state["music"]
    
    def is_motion(self):
        return self.state["motion"]
    
    def set_state_true(self, state_name: str):
        for key in self.state:
            if key == state_name:
                self.state[key] = True
            else:
                self.state[key] = False

    def set_motion(self, motion_name: str):
        self.motion_now = motion_name

    def _load_model_parameters(self, model: live2d.LAppModel):
        for i in range(model.GetParameterCount()):
            param = model.GetParameter(i)
            self.model_params[param.id] = param.default
            self.model_params_range[param.id] = {
                "min": param.min,
                "max": param.max,
                "default": param.default
            }

    def get_param_default(self):
        default = {}
        for param_name, value in self.model_params_range.items():
            default[param_name] = value["default"]
        return default

    def _load_physics(self):
        """从 *.physics3.json 文件中加载模型参数"""
        physics3_file_path = None
        for file_name in os.listdir(self.l2d_folder_name):
            if file_name.endswith(".physics3.json"):
                physics3_file_path = os.path.join(self.l2d_folder_name, file_name)
                break

        with open(physics3_file_path, "r", encoding="utf-8") as f:
            physics3_data = json.load(f)
        
        self.l2d_physics = Live2DPhysics(
            self.model,
            self.model_params,
            self.model_params_range,
            physics3_data["Meta"]["PhysicsSettingCount"],
            physics3_data["Meta"]["PhysicsDictionary"]
        )
        self.l2d_physics.set_physics_settings(physics3_data["PhysicsSettings"])
    
    def load_l2d_model(self):
        model_json_path = None
        for file_name in os.listdir(self.l2d_folder_name):
            if file_name.endswith(".model3.json"):
                model_json_path = os.path.join(self.l2d_folder_name, file_name)
                break

        self.model = live2d.LAppModel()
        self.model.LoadModelJson(model_json_path)

        self.model.SetAutoBreathEnable(self.config_editor.auto_breath)
        self.model.SetAutoBlinkEnable(self.config_editor.auto_blink)

        self._load_model_parameters(self.model)
        self._load_physics()
    
    def l2d_and_glew_init(self):
        live2d.init()
        # live2d.glewInit()
        live2d.glInit()

    def params_update(self):
        if not self.model:
            return
        
        if self.is_motion():
            posture, end = self.motion_manager.get_motion_posture(self.motion_now)
            self.model_params.update(posture)
            if end:
                self.set_state_true("track")
                self.to_default = 0.1 * self.config_editor.refresh_rate

        else:
            self.model_params.update(self.l2d_physics.update_model_params(self.model_params, 1 / self.config_editor.refresh_rate, self.velocity))

        for param_name, param_value in self.model_params.items():
            if self.config_editor.auto_breath and param_name == "ParamBreath":
                continue

            if self.config_editor.auto_blink and param_name in ["ParamEyeLOpen", "ParamEyeROpen"]:
                continue

            self.model.SetParameterValue(param_name, param_value, 1 / self.config_editor.refresh_rate * 30)
    
    def param_to_default(self):
        self.model_params.update(self.get_param_default())
