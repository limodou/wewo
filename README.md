wewo
====

Wewo is a simple workflow. It's inspired by zope.wfmc. But it just *looks* like it. Because I'll add functions what I want. I need a real asynchronized workload engine to suit my web environment. 

I'll follow the WFMC sepcification as I can, but I just need a simple engine, so it may not very compatible with WFMC. But the most terms will be the same.

Process
  This object describes one particular work process inside the
  workflow of an entity. 

Activity
  The activity describes one step inside a process. During an
  activity, multiple tools (defined via applications) are called to interact
  with software and also change workflow-relevant data. When all
  tools are finished the activity will transition to the next one. 

Transition
  This object, as the name suggests, represents a transition
  from one activity to another. This object does not have a rich API and
  merely defines a condition that decides whether a particular transition
  can be done. 

Application
  An application is a piece of software that is executed. One
  can think of it more of less as a function. The input parameters
  (arguments of the function) can be specified and must be variables from
  the workflow-relevant data. The application's output parameters (return
  values) are stored as workflow-relevant data, overwriting existing data as
  necessary. Applications can require manual input. 

Participant
  The participant is the actor/principal that is completing a
  particular activity. 

Workflow Relevant Data
  This data (WfRD) contains values that are
  necessary for the workflow function, either by calling applications or
  evaluating conditions (for example during transitions). Th input and
  output data of a process can be specified in its formal parameters and
  will be stored or looked up in the WfRD, respectively. 

And I think the Process and WorkItem should be stored persistantly, such as in Database. And the workflow engine maybe a deamon program. This engine should also support Participant and user interface, but I think it's not the primary component of this workflow. But I still want to configure them in configuration file, so that I can automatically create the interface very dynamically.