#!/usr/bin/env python
from __future__ import print_function

"""
/ground_truth   nav_msgs/Odometry
/cmd_vel        geometry_msgs/Twist
"""

import rospy
import nav_msgs.msg as navmsg
import geometry_msgs.msg as geommsg
import std_msgs.msg as stdmmsg
from datetime import date


pub_str = rospy.Publisher("race_info", stdmmsg.String, queue_size = 1)
pub_speed = rospy.Publisher("speed_measured", stdmmsg.Float32, queue_size = 1)
pub_dist = rospy.Publisher("dist_measured", stdmmsg.Float32, queue_size = 1)
pub_time = rospy.Publisher("race_time", stdmmsg.Float32, queue_size = 1)
prev_point = geommsg.Point()
prev_time = stdmmsg.Header()
first_run_pose = True
first_run_cmd = True
first_run_end = True
race_start_time = -1
reset = False
race_started = False
race_duration = 120 # seconds
kozepiskola_nev = "--"
kozepiskola_id = "--"
dist = 0.0 # dist = ket pont euklideszi tavolsaga, szummazva

def cmd_vel_callback(cmd):
    global race_started, first_run_cmd, race_start_time, kozepiskola_nev
    #rospy.loginfo("cmd: %.2f", cmd.linear.x)
    race_started = True
    if first_run_cmd:      
        race_start_time = rospy.get_rostime()
        rospy.loginfo("A verseny elindult jelenlegi versenyzo: %s" % (kozepiskola_nev))
        first_run_cmd = False

def ground_truth_callback(data):
    global prev_point, prev_time, first_run_pose, reset, dist, race_started, race_start_time, first_run_end, kozepiskola_nev, kozepiskola_id
    race_info_str = stdmmsg.String()
    if first_run_pose:      
        first_run_pose = False
        prev_point.x = data.pose.pose.position.x
        prev_point.y = data.pose.pose.position.y
        prev_time = data.header
    else:
        if reset:
            dist = 0.0
        meters_d = ((data.pose.pose.position.x - prev_point.x)**2 + (data.pose.pose.position.y - prev_point.y)**2) ** 0.5
        sec_s = (data.header.stamp - prev_time.stamp).to_sec()
        dist += meters_d
        speed = meters_d / sec_s
        if race_started:
            time_since_start = (data.header.stamp - race_start_time).to_sec()
            #rospy.loginfo("dist: %.4f", dist)
            #rospy.loginfo("speed: %.20f", speed)
            #rospy.loginfo("meters: %.10f sec: %.4f", meters_d, sec_s)
            #rospy.loginfo("time_since_start: %.2f", time_since_start)
            m, s = divmod(time_since_start, 60)
            race_info_str.data = "Verseny ido: %1d:%05.2f" % (m,s)
            race_info_str.data += "\nMegtett tav: %.2f meter" % (dist)
            race_info_str.data += "\nPillanatnyi sebesseg: %.2f m/s" % (speed)
            try:
                race_info_str.data += "\nAtlag sebesseg: %.2f m/s" % (dist / time_since_start)
            except: None
            if race_duration < time_since_start:
                race_info_str.data = "A verseny vegetert"
                if first_run_end:      
                    first_run_end = False
                    rospy.loginfo("A verseny vegetert")
                    rospy.loginfo("<tr><td>%s</td><td>%.3f</td><td>(kesobb)</td><td>%s (versenyen kivul)</td></tr>" % (kozepiskola_id, dist, date.today().strftime("%Y.%m.%.d")))
        else:
            time_since_start = -1.0
            race_info_str.data = "A verseny meg nem indult el (nincs /cmd_vel)"
        prev_point.x = data.pose.pose.position.x
        prev_point.y = data.pose.pose.position.y
        prev_time = data.header
        pub_str.publish(race_info_str)
        pub_speed.publish(speed)
        pub_dist.publish(dist)
        pub_time.publish(time_since_start)
    #rospy.loginfo("x: %.2f, y: %.2f", data.pose.pose.position.x, data.pose.pose.position.y)

def iskola_callback(teljes):
    global kozepiskola_nev, kozepiskola_id
    kozepiskola_nev = teljes.data[0:-5] 
    kozepiskola_id = teljes.data[-4:-1] 


if __name__ == '__main__':
    rospy.init_node("measure_gazebo_race_data")
    rospy.loginfo(rospy.get_name() + " started")
    rospy.Subscriber("ground_truth", navmsg.Odometry, ground_truth_callback)
    rospy.Subscriber("cmd_vel", geommsg.Twist, cmd_vel_callback)
    rospy.Subscriber("kozepiskola", stdmmsg.String, iskola_callback)
    rospy.spin()
