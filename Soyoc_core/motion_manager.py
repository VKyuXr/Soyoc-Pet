import Soyoc_core.config_editor as Soyoc_config
import os
import json
import datetime

class StraightLine:
    def __init__(self, start_point: list[float], end_point: list[float]):
        self.start_time = start_point[0]
        self.start_value = start_point[1]
        self.end_time = end_point[0]
        self.end_value = end_point[1]

    def get_value(self, t: float):
        if t < self.start_time or t > self.end_time:
            raise ValueError(f"StraightLine: time must be between {self.start_time} and {self.end_time}, but got {t}")
        if self.start_time == self.end_time:
            return self.start_value
        ratio = (t - self.start_time) / (self.end_time - self.start_time)
        return self.start_value + ratio * (self.end_value - self.start_value)

class BezierCurve:
    def __init__(self, start_point: list[float], control_point: list[float], end_point: list[float]):
        self.start_point = start_point  # [t0, v0]
        self.control1 = control_point[0:2]  # [t1, v1]
        self.control2 = control_point[2:4]  # [t2, v2]
        self.end_point = end_point  # [t3, v3]

    def get_value(self, t: float):
        t0, v0 = self.start_point
        t3, v3 = self.end_point
        if t < t0 or t > t3:
            raise ValueError(f"BezierCurve: time must be between {t0} and {t3}, but got {t}")

        # 二分法求解贝塞尔曲线x(t)=target_time的k值
        def bezier_x(k):
            return ( (1 - k)**3 * t0 +
                     3 * (1 - k)**2 * k * self.control1[0] +
                     3 * (1 - k) * k**2 * self.control2[0] +
                     k**3 * t3 )

        low, high = 0.0, 1.0
        epsilon = 1e-6
        for _ in range(100):  # 最多迭代100次
            mid = (low + high) / 2
            current_t = bezier_x(mid)
            if abs(current_t - t) < epsilon:
                break
            if current_t < t:
                low = mid
            else:
                high = mid

        k = (low + high) / 2

        # 计算对应的值
        value = ( (1 - k)**3 * v0 +
                  3 * (1 - k)**2 * k * self.control1[1] +
                  3 * (1 - k) * k**2 * self.control2[1] +
                  k**3 * v3 )
        return value

class Motion:
    def __init__(self, name: str, group: str, index: int):
        self.name = name
        self.group = group
        self.index = index
        self.curves = {}
    
    def set_info(self, duration: float, fps: int):
        self.duration = duration
        self.fps = fps
    
    def add_curve(self, param_name: str, curve_data: list):
        start_time_list = []
        end_time_list = []
        curve_list = []
        current_start_time = curve_data[0]  # 初始时间

        i = 0
        start_point = curve_data[i:i+2]
        i += 2

        while i < len(curve_data):
            if i >= len(curve_data):
                break
            line_type = curve_data[i]
            i += 1

            if line_type == 0:  # 直线
                end_point = curve_data[i:i+2]
                i += 2
                start_time_list.append(current_start_time)
                end_time = end_point[0]
                end_time_list.append(end_time)
                curve_list.append(StraightLine(start_point, end_point))
                current_start_time = end_time
                start_point = end_point

            elif line_type == 1:  # 曲线
                control_point = curve_data[i:i+4]
                i += 4
                end_point = curve_data[i:i+2]
                i += 2
                start_time_list.append(current_start_time)
                end_time = end_point[0]
                end_time_list.append(end_time)
                curve_list.append(BezierCurve(start_point, control_point, end_point))
                current_start_time = end_time
                start_point = end_point

        self.curves[param_name] = {
            "start_time": start_time_list,
            "end_time": end_time_list,
            "curve": curve_list
        }
    
    def get_posture(self, time: float):
        posture = {}
        for param_name, curve_param in self.curves.items():
            for i in range(len(curve_param["curve"])):
                start = curve_param["start_time"][i]
                end = curve_param["end_time"][i]
                if start <= time <= end:
                    posture[param_name] = curve_param["curve"][i].get_value(time)
                    break  # 找到后跳出循环
        return posture

class AnimationController:
    def __init__(self):
        self.start_time = None

    def set_start_time(self):
        self.start_time = datetime.datetime.now()
    
    def get_duration(self):
        if not self.start_time:
            return 0.0
        return (datetime.datetime.now() - self.start_time).total_seconds()

    def destroy(self):
        self.start_time = None

class MotionManager:
    def __init__(self, config_editor):
        self.config_editor = config_editor
        self.motion_list = []
        self._init_motions()
        self.motion_now: Motion = None
        self.animation = AnimationController()

    def set_motion_end_callback(self, callback_function):
        self.motion_end_callback = callback_function

    def _init_motions(self):
        motion_path = os.path.join(self.config_editor.main_dir, self.config_editor.l2d_model, "motion")
        motion_tree_info = self.config_editor.motions

        for motion_name, group_and_index in motion_tree_info.items():
            file_path = os.path.join(motion_path, motion_name + ".motion3.json")
            with open(file_path, "r", encoding="utf-8") as file:
                json_data = json.load(file)

            motion = Motion(motion_name, group_and_index["group"], group_and_index["index"])
            motion.set_info(json_data["Meta"]["Duration"], json_data["Meta"]["Fps"])
            for curve in json_data["Curves"]:
                if "Param" in curve["Id"]:
                    motion.add_curve(curve["Id"], curve["Segments"])
            self.motion_list.append(motion)

    def get_motion_posture(self, motion_name: str):
        # 动画已结束且未找到动作时返回空
        if self.motion_now is None:
            # 寻找对应动作
            target_motion = None
            for motion in self.motion_list:
                if motion.name == motion_name:
                    target_motion = motion
                    break
            if not target_motion:
                return {}
            self.motion_now = target_motion
            self.animation.set_start_time()

        current_duration = self.animation.get_duration()
        if current_duration <= self.motion_now.duration:
            end = 0
            return self.motion_now.get_posture(current_duration), end
        else:  # 动画结束后返回最后一帧
            end = 1
            final_posture = self.motion_now.get_posture(self.motion_now.duration)
            self.motion_now = None
            self.animation.destroy()
            return final_posture, end