import numpy as np

class PhysicsSimulator:
    def __init__(self, 
                 strand_count: int,
                 particle_radius: list,  # 输入为列表
                 delay: list,            # 输入为列表
                 acceleration: list,     # 输入为列表
                 mobility: list,         # 输入为列表
                 gravity: list = [0.0, -1],  # 新增重力参数
                 air_resistance: float = 1.0,
                 movement_threshold: float = 0.01):
        """
        :param strand_count: 粒子总数
        :param particle_radius: 每个粒子的半径列表，长度需为 strand_count
        :param delay: 每个粒子的延迟列表，长度需为 strand_count
        :param acceleration: 每个粒子的加速度列表，长度需为 strand_count
        :param mobility: 每个粒子的移动性列表，长度需为 strand_count
        :param air_resistance: 空气阻力系数
        :param movement_threshold: 移动阈值
        """
        # 参数验证
        if not all(isinstance(lst, list) for lst in [particle_radius, delay, acceleration, mobility]):
            raise TypeError("particle_radius, delay, acceleration, mobility 必须为列表")
        
        if not all(len(lst) == strand_count for lst in [particle_radius, delay, acceleration, mobility]):
            raise ValueError(f"所有参数列表长度必须等于 strand_count ({strand_count})")

        # 转换为 NumPy 数组以优化计算
        self.strand_count = strand_count
        self.gravity = np.array(gravity, dtype=np.float32)
        self.particles = {
            'position': np.zeros((strand_count, 2), dtype=np.float32),
            'velocity': np.zeros((strand_count, 2), dtype=np.float32),
            'last_position': np.zeros((strand_count, 2), dtype=np.float32),
            'last_gravity': np.tile(self.gravity, (strand_count, 1)),
            'radius': np.array(particle_radius, dtype=np.float32),
            'delay': np.array(delay, dtype=np.float32),
            'acceleration': np.array(acceleration, dtype=np.float32),
            'mobility': np.array(mobility, dtype=np.float32)
        }
        
        # 环境参数
        self.air_resistance = air_resistance
        self.threshold = movement_threshold

    def update(self,
               delta_time: float,
               total_translation: list = [0.0, 0.0],
               total_angle: float = 0.0,
               wind_direction: list = [0.0, 0.0]):
        """
        :param delta_time: 时间步长 (秒)
        :param total_translation: 根节点位移 (形如 [x, y] 的列表)
        :param total_angle: 整体旋转角度 (度)
        :param wind_direction: 风力方向 (形如 [x, y] 的列表)
        """
        # 将输入列表转换为 NumPy 数组
        total_translation = np.array(total_translation, dtype=np.float32)
        wind_direction = np.array(wind_direction, dtype=np.float32)

        # 更新根节点位置
        self.particles['position'][0] = total_translation

        # 修改重力方向计算（现在基于输入重力）
        total_radian = np.deg2rad(total_angle)
        rotation_matrix = np.array([
            [np.cos(total_radian), -np.sin(total_radian)],
            [np.sin(total_radian), np.cos(total_radian)]
        ])
        current_gravity = rotation_matrix @ self.gravity  # 旋转基础重力

        # 保持单位向量特性
        gravity_norm = np.linalg.norm(current_gravity)
        if gravity_norm > 1e-6:
            current_gravity /= gravity_norm

        # 更新粒子状态
        for i in range(1, self.strand_count):
            prev_idx = i-1
            curr_idx = i

            # 保存上一帧位置
            self.particles['last_position'][curr_idx] = self.particles['position'][curr_idx]

            # 计算受力
            gravity_force = current_gravity * self.particles['acceleration'][curr_idx]
            total_force = gravity_force + wind_direction

            # 应用延迟
            effective_delay = self.particles['delay'][curr_idx] * delta_time * 30

            # 计算方向变化
            direction = self.particles['position'][curr_idx] - self.particles['position'][prev_idx]
            
            # 计算角度差
            last_gravity = self.particles['last_gravity'][curr_idx]
            angle_diff = np.arctan2(
                np.cross(last_gravity, current_gravity),
                np.dot(last_gravity, current_gravity)
            )
            radian = angle_diff / self.air_resistance

            # 应用旋转
            cos_r, sin_r = np.cos(radian), np.sin(radian)
            rotation_matrix = np.array([[cos_r, -sin_r], [sin_r, cos_r]])
            rotated_direction = rotation_matrix @ direction

            # 计算新位置
            base_pos = self.particles['position'][prev_idx] + rotated_direction
            velocity_effect = self.particles['velocity'][curr_idx] * effective_delay
            force_effect = total_force * (effective_delay ** 2)
            new_pos = base_pos + velocity_effect + force_effect

            # 约束长度
            new_dir = new_pos - self.particles['position'][prev_idx]
            # if new_dir == [0, 0] and new_dir == [0, 0]:
            #     unit_dir = 1
            # else:
            unit_dir = new_dir / np.linalg.norm(new_dir)
            constrained_pos = self.particles['position'][prev_idx] + unit_dir * self.particles['radius'][curr_idx]

            # 应用移动阈值
            if abs(constrained_pos[0]) < self.threshold:
                constrained_pos[0] = 0.0
            self.particles['position'][curr_idx] = constrained_pos

            # 更新速度
            if effective_delay != 0:
                delta_pos = self.particles['position'][curr_idx] - self.particles['last_position'][curr_idx]
                self.particles['velocity'][curr_idx] = delta_pos * (self.particles['mobility'][curr_idx] / effective_delay)
            else:
                self.particles['velocity'][curr_idx] = np.zeros(2, dtype=np.float32)

            # 更新重力记录
            self.particles['last_gravity'][curr_idx] = current_gravity

    @property
    def positions(self) -> list:
        """获取所有粒子位置 (返回列表的列表)"""
        return [pos.tolist() for pos in self.particles['position']]
    
    def change_gravity(self, inertial_force: list):
        # 将输入转换为 numpy 数组
        inertial_force = np.array(inertial_force, dtype=np.float32)
        if np.linalg.norm(inertial_force) != 0:
            inertial_force = inertial_force / np.linalg.norm(inertial_force)
        
        self.gravity = [0, -1] + np.array(inertial_force, dtype=np.float32) * 0.9
        self.gravity = self.gravity / np.linalg.norm(self.gravity)

class PhysicsSetting:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.input_params = []
        self.output_params = []
        self.physics_simulator: PhysicsSimulator
    
    def get_id(self):
        return self.id
    
    def add_input_param(self, input_params: list[dict]):
        for input_param in input_params:
            self.input_params.append(
                {
                    "id": input_param["Source"]["Id"],
                    "weight": input_param["Weight"] / 100,
                    "reflect": input_param["Reflect"]
                }
            )
    
    def add_output_param(self, output_params: list[dict]):
        for output_param in output_params:
            self.output_params.append(
                {
                    "id": output_param["Destination"]["Id"],
                    "weight": output_param["Weight"] / 100,
                    "reflect": output_param["Reflect"]
                }
            )
    
    def add_physics_simulator(self, count: int, mobility: list, delay: list, acceleration: list, radius: list):
        self.physics_simulator = PhysicsSimulator(
            strand_count=count,
            mobility=mobility,
            delay=delay,
            acceleration=acceleration,
            particle_radius=radius,
        )
    
    def calculate_output_delta(self, model_params: list, delta_t: float):
        delta_input = 0
        for input_param in self.input_params:
            if input_param["reflect"]:
                delta_input -= model_params[input_param["id"]] * input_param["weight"]
            else:
                delta_input += model_params[input_param["id"]] * input_param["weight"]
        
        self.physics_simulator.update(delta_time=delta_t, total_translation=[delta_input, 0])
        delta_output = self.physics_simulator.positions[-1][0] - self.physics_simulator.positions[0][0]

        output_delta = {}
        for output_param in self.output_params:
            if output_param["reflect"]:
                output_delta[output_param["id"]] = - delta_output * output_param["weight"]
            else:
                output_delta[output_param["id"]] = delta_output * output_param["weight"]
        return output_delta

    def inertial_simulation(self, velocity: list, delta_t: float):
        mass = 1
        gravity = [- mass * velocity[0] / delta_t, - mass * velocity[1] / delta_t]
        self.physics_simulator.change_gravity(gravity)
