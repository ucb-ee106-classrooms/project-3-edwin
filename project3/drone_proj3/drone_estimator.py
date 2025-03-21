import matplotlib.pyplot as plt
import numpy as np
import time
plt.rcParams['font.family'] = ['Arial']
plt.rcParams['font.size'] = 14


class Estimator:
    """A base class to represent an estimator.

    This module contains the basic elements of an estimator, on which the
    subsequent DeadReckoning, Kalman Filter, and Extended Kalman Filter classes
    will be based on. A plotting function is provided to visualize the
    estimation results in real time.

    Attributes:
    ----------
        u : list
            A list of system inputs, where, for the ith data point u[i],
            u[i][1] is the thrust of the quadrotor
            u[i][2] is right wheel rotational speed (rad/s).
        x : list
            A list of system states, where, for the ith data point x[i],
            x[i][0] is translational position in x (m),
            x[i][1] is translational position in z (m),
            x[i][2] is the bearing (rad) of the quadrotor
            x[i][3] is translational velocity in x (m/s),
            x[i][4] is translational velocity in z (m/s),
            x[i][5] is angular velocity (rad/s),
        y : list
            A list of system outputs, where, for the ith data point y[i],
            y[i][1] is distance to the landmark (m)
            y[i][2] is relative bearing (rad) w.r.t. the landmark
        x_hat : list
            A list of estimated system states. It should follow the same format
            as x.
        dt : float
            Update frequency of the estimator.
        fig : Figure
            matplotlib Figure for real-time plotting.
        axd : dict
            A dictionary of matplotlib Axis for real-time plotting.
        ln* : Line
            matplotlib Line object for ground truth states.
        ln_*_hat : Line
            matplotlib Line object for estimated states.
        canvas_title : str
            Title of the real-time plot, which is chosen to be estimator type.

    Notes
    ----------
        The landmark is positioned at (0, 5, 5).
    """
    # noinspection PyTypeChecker
    def __init__(self, is_noisy=False):
        self.u = []
        self.x = []
        self.y = []
        self.x_hat = []  # Your estimates go here!
        self.t = []
        self.fig, self.axd = plt.subplot_mosaic(
            [['xz', 'phi'],
             ['xz', 'x'],
             ['xz', 'z']], figsize=(20.0, 10.0))
        self.ln_xz, = self.axd['xz'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_xz_hat, = self.axd['xz'].plot([], 'o-c', label='Estimated')
        self.ln_phi, = self.axd['phi'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_phi_hat, = self.axd['phi'].plot([], 'o-c', label='Estimated')
        self.ln_x, = self.axd['x'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_x_hat, = self.axd['x'].plot([], 'o-c', label='Estimated')
        self.ln_z, = self.axd['z'].plot([], 'o-g', linewidth=2, label='True')
        self.ln_z_hat, = self.axd['z'].plot([], 'o-c', label='Estimated')
        self.canvas_title = 'N/A'

        # Defined in dynamics.py for the dynamics model
        # m is the mass and J is the moment of inertia of the quadrotor 
        self.gr = 9.81 
        self.m = 0.92
        self.J = 0.0023
        # These are the X, Y, Z coordinates of the landmark
        self.landmark = (0, 5, 5)

        # This is a (N,12) where it's time, x, u, then y_obs 
        if is_noisy:
            with open('noisy_data.npy', 'rb') as f:
                self.data = np.load(f)
        else:
            with open('data.npy', 'rb') as f:
                self.data = np.load(f)

        self.dt = self.data[-1][0]/self.data.shape[0]


    def run(self):
        avg_time = 0
        n = 0
        for i, data in enumerate(self.data):
            self.t.append(np.array(data[0]))
            self.x.append(np.array(data[1:7]))
            self.u.append(np.array(data[7:9]))
            self.y.append(np.array(data[9:12]))
            if i == 0:
                self.x_hat.append(self.x[-1])
            else:
                start_time = time.time()                
                self.update(i)
                end_time = time.time()
                avg_time += end_time - start_time
                n += 1

        print("Average time is: ", avg_time/n)
        self.calcError()
        return self.x_hat
    
    def calcError(self):

        absErrorX = 0
        absErrorZ = 0
        absErrorPhi = 0
        absErrorDist = 0
        relErrorX = 0
        relErrorZ = 0
        relErrorPhi = 0
        relErrorDist = 0
        
        for i in range(len(self.x)):
            # Calculate absolute errors
            absX = abs(self.x[i][0] - self.x_hat[i][0])
            absZ = abs(self.x[i][1] - self.x_hat[i][1])
            absPhi = abs(self.x[i][2] - self.x_hat[i][2])
            
            # Calculate distances to landmark for true and estimated state
            true_dist = np.sqrt((self.landmark[0] - self.x[i][0])**2 + 
                            self.landmark[1]**2 + 
                            (self.landmark[2] - self.x[i][1])**2)
            
            est_dist = np.sqrt((self.landmark[0] - self.x_hat[i][0])**2 + 
                            self.landmark[1]**2 + 
                            (self.landmark[2] - self.x_hat[i][1])**2)
            
            absDist = abs(true_dist - est_dist)
            
            # Sum up absolute errors
            absErrorX += absX
            absErrorZ += absZ
            absErrorPhi += absPhi
            absErrorDist += absDist
            
            # Calculate relative errors
            if abs(self.x[i][0]) > 1e-10:
                relErrorX += absX / abs(self.x[i][0])
            if abs(self.x[i][1]) > 1e-10:
                relErrorZ += absZ / abs(self.x[i][1])
            if abs(self.x[i][2]) > 1e-10:
                relErrorPhi += absPhi / abs(self.x[i][2])
            if true_dist > 1e-10:
                relErrorDist += absDist / true_dist
        
        # Calculate average errors
        n = len(self.x)
        if n > 0:
            absErrorX /= n
            absErrorZ /= n
            absErrorPhi /= n
            absErrorDist /= n
            relErrorX /= n
            relErrorZ /= n
            relErrorPhi /= n
            relErrorDist /= n
        
        print("Absolute Errors:")
        print(f"X Position: {absErrorX:.6f} m")
        print(f"Z Position: {absErrorZ:.6f} m")
        print(f"Phi Angle: {absErrorPhi:.6f} rad")
        print(f"Distance to Landmark: {absErrorDist:.6f} m")
        print("\nRelative Errors:")
        print(f"X Position: {relErrorX:.6f} (ratio)")
        print(f"Z Position: {relErrorZ:.6f} (ratio)")
        print(f"Phi Angle: {relErrorPhi:.6f} (ratio)")
        print(f"Distance to Landmark: {relErrorDist:.6f} (ratio)")



    def update(self, _):
        raise NotImplementedError

    def plot_init(self):
        self.axd['xz'].set_title(self.canvas_title)
        self.axd['xz'].set_xlabel('x (m)')
        self.axd['xz'].set_ylabel('z (m)')
        self.axd['xz'].set_aspect('equal', adjustable='box')
        self.axd['xz'].legend()
        self.axd['phi'].set_ylabel('phi (rad)')
        self.axd['phi'].set_xlabel('t (s)')
        self.axd['phi'].legend()
        self.axd['x'].set_ylabel('x (m)')
        self.axd['x'].set_xlabel('t (s)')
        self.axd['x'].legend()
        self.axd['z'].set_ylabel('z (m)')
        self.axd['z'].set_xlabel('t (s)')
        self.axd['z'].legend()
        plt.tight_layout()

    def plot_update(self, _):
        self.plot_xzline(self.ln_xz, self.x)
        self.plot_xzline(self.ln_xz_hat, self.x_hat)
        self.plot_philine(self.ln_phi, self.x)
        self.plot_philine(self.ln_phi_hat, self.x_hat)
        self.plot_xline(self.ln_x, self.x)
        self.plot_xline(self.ln_x_hat, self.x_hat)
        self.plot_zline(self.ln_z, self.x)
        self.plot_zline(self.ln_z_hat, self.x_hat)

    def plot_xzline(self, ln, data):
        if len(data):
            x = [d[0] for d in data]
            z = [d[1] for d in data]
            ln.set_data(x, z)
            self.resize_lim(self.axd['xz'], x, z)

    def plot_philine(self, ln, data):
        if len(data):
            t = self.t
            phi = [d[2] for d in data]
            ln.set_data(t, phi)
            self.resize_lim(self.axd['phi'], t, phi)

    def plot_xline(self, ln, data):
        if len(data):
            t = self.t
            x = [d[0] for d in data]
            ln.set_data(t, x)
            self.resize_lim(self.axd['x'], t, x)

    def plot_zline(self, ln, data):
        if len(data):
            t = self.t
            z = [d[1] for d in data]
            ln.set_data(t, z)
            self.resize_lim(self.axd['z'], t, z)

    # noinspection PyMethodMayBeStatic
    def resize_lim(self, ax, x, y):
        xlim = ax.get_xlim()
        ax.set_xlim([min(min(x) * 1.05, xlim[0]), max(max(x) * 1.05, xlim[1])])
        ylim = ax.get_ylim()
        ax.set_ylim([min(min(y) * 1.05, ylim[0]), max(max(y) * 1.05, ylim[1])])

class OracleObserver(Estimator):
    """Oracle observer which has access to the true state.

    This class is intended as a bare minimum example for you to understand how
    to work with the code.

    Example
    ----------
    To run the oracle observer:
        $ python drone_estimator_node.py --estimator oracle_observer
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Oracle Observer'

    def update(self, _):
        self.x_hat.append(self.x[-1])


class DeadReckoning(Estimator):
    """Dead reckoning estimator.

    Your task is to implement the update method of this class using only the
    u attribute and x0. You will need to build a model of the unicycle model
    with the parameters provided to you in the lab doc. After building the
    model, use the provided inputs to estimate system state over time.

    The method should closely predict the state evolution if the system is
    free of noise. You may use this knowledge to verify your implementation.

    Example
    ----------
    To run dead reckoning:
        $ python drone_estimator_node.py --estimator dead_reckoning
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Dead Reckoning'

    def update(self, _):
        
        if len(self.x_hat) > 0:
            
            # TODO: Your implementation goes here!
            # You may ONLY use self.u and self.x[0] for estimation
            t = len(self.x_hat)
            phi = self.x[t-1][2]
            x_dot = self.x[t-1][3]
            z_dot = self.x[t-1][4]
            phi_dot = self.x[t-1][5]
            A = np.array([[0, 0],
                             [0, 0],
                             [0, 0],
                             [-np.sin(phi) / self.m, 0],
                             [np.cos(phi) / self.m, 1],
                             [0, 1 / self.J]])
            b = np.array([x_dot, z_dot, phi_dot, 0, - self.gr, 0])
            new = self.x_hat[t-1] + (b + A @ self.u[t]) * self.dt
            self.x_hat.append(new)
            # raise NotImplementedError

# noinspection PyPep8Naming
class ExtendedKalmanFilter(Estimator):
    """Extended Kalman filter estimator.

    Your task is to implement the update method of this class using the u
    attribute, y attribute, and x0. You will need to build a model of the
    unicycle model and linearize it at every operating point. After building the
    model, use the provided inputs and outputs to estimate system state over
    time via the recursive extended Kalman filter update rule.

    Hint: You may want to reuse your code from DeadReckoning class and
    KalmanFilter class.

    Attributes:
    ----------
        landmark : tuple
            A tuple of the coordinates of the landmark.
            landmark[0] is the x coordinate.
            landmark[1] is the y coordinate.
            landmark[2] is the z coordinate.

    Example
    ----------
    To run the extended Kalman filter:
        $ python drone_estimator_node.py --estimator extended_kalman_filter
    """
    def __init__(self, is_noisy=False):
        super().__init__(is_noisy)
        self.canvas_title = 'Extended Kalman Filter'
        # TODO: Your implementation goes here!
        # You may define the Q, R, and P matrices below.
        self.A = np.identity(4)
        # self.B = np.array([
        #         [((self.r * np.cos(np.pi / 4)) / 2), ((self.r * np.cos(np.pi / 4))/ 2)],
        #         [((self.r * np.sin(np.pi / 4)) / 2), ((self.r * np.sin(np.pi / 4))/ 2)],
        #         [1, 0],
        #         [0, 1]]) * self.dt
        self.C = np.array([[1,0,0,0],
                      [0,1,0,0]])
        self.Q = np.diag([0.05, 0.1, 1000, 0.05, 0.05, 0.5])
        
        self.R = np.diag([1000, 2])
        
        self.P = np.diag([0.05, 0.1, 1000, 0.05, 0.05, 0.5])

    # noinspection DuplicatedCode
    def update(self, i):
        if len(self.x_hat) > 0: #and self.x_hat[-1][0] < self.x[-1][0]:
            # TODO: Your implementation goes here!
            # You may use self.u, self.y, and self.x[0] for estimation
            A = self.A
            # print(len(self.x_hat), len(self.x_hat[0]), self.x_hat)
            # B = self.B
            C = self.C
            P = self.P
            Q = self.Q
            R = self.R
            t = len(self.x_hat)

    
            # print("x_hat: ", self.x_hat[t-1])
            # print(self.u[t-1])

            x_prediction = self.g(self.x_hat[t-1], self.u[t-1])
            A = self.approx_A(self.x_hat[t-1], self.u[t-1])
            P = A @ P @ A.T + Q
            C = self.approx_C(x_prediction)
            K = P @ C.T @ np.linalg.inv(C @ P @ C.T + R)
            new = x_prediction + K @ (self.y[t] - self.h(x_prediction))

            self.P = (np.identity(6) - (K @ C)) @ P
            self.x_hat.append(new)


    def g(self, x, u):
        phi = x[2]
        x_dot = x[3]
        z_dot = x[4]
        phi_dot = x[5]
        A = np.array([[0, 0],
                            [0, 0],
                            [0, 0],
                            [-np.sin(phi) / self.m, 0],
                            [np.cos(phi) / self.m, 0],
                            [0, 1 / self.J]])
        b = np.array([x_dot, z_dot, phi_dot, 0, - self.gr, 0])
        g = x + (b + A @ u) * self.dt
        return g

    def h(self, x):
        l_x = 0
        l_y = 5
        l_z = 5

        d = np.sqrt((l_x - x[0]) ** 2 + l_y**2 + (l_z - x[1])**2)


        phi = x[2]


        return np.array([d, phi])

    def approx_A(self, x, u):
        J = np.eye(6)
        J[0, 3] = self.dt
        J[1, 4] = self.dt
        J[2, 5] = self.dt
        J[3, 2] = -self.dt * np.cos(x[2]) / self.m * u[0]
        J[4, 2] = -self.dt * np.sin(x[2]) / self.m * u[0]

        return J
        

    def approx_C(self, x):
        l_x = 0
        l_y = 5
        l_z = 5

        d = np.sqrt((l_x - x[0]) ** 2 + l_y**2 + (l_z - x[1])**2)

        jac = np.zeros((2, 6))
        jac[0, 0] = (x[0] - l_x) / d
        jac[0, 1] = (x[1] - l_z) / d
        jac[1, 2] = 1

        return jac

