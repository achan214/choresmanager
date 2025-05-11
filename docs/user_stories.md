
**User Story 1: Adding a Chore**

As a roommate group admin,
I want to create a new chore and assign it to one or more members of my group,
so that everyone knows what tasks they are responsible for.

Write operation (creating a chore)
Persona = admin user

Exception: Missing Required Chore Info  
Scenario: A roommate group admin tries to create a chore without entering a name or due date.  
Handling: The system will show an error message like "Please enter a chore name and due date" and will not allow the chore to be created until those fields are filled in.  

**User Story 2: Marking a Chore as Complete**

As a roommate,
I want to mark a chore as completed, so that the group can see that it's done and avoid duplicate effort.

Write operation (updating chore status)  
Persona = regular roommate member  

Exception: Unauthorized Chore Deletion  
Scenario: A regular roommate (non-admin) tries to delete a chore they did not create.  
Handling: The system will prevent the action and display a message like "Only the chore creator or a group admin can delete this task."  

**User Story 3: Viewing the Chore Schedule**

As a busy student,
I want to view all my assigned chores for the current week, so that I can manage my time effectively around my other commitments.

Read operation (retrieving schedule)  
Persona = time-conscious student user  

Exception: No Chores Assigned for the Week  
Scenario: A student opens the app to view their schedule but has not been assigned any chores for the current week.  
Handling: The system could display a message like: “Check the full group chore list or ask your group admin if you’d like to help out.”  

**User Story 4: Joining a Roommate Group**

As a new user,
I want to join an existing group using an invite code, so that I can start managing chores collaboratively with my roommates.

Write operation (joining group)  
Persona = new user  

Exception: Invalid Group Invite Code  
Scenario: A user attempts to join a roommate group using an invalid or expired invite code.  
Handling: The system will return an error message such as "Invalid invite code. Please check and try again or request a new code from your group admin."  

**User Story 5: Creating a Roommate Group**

As a college student,
I want to create a new roommate group, so that I can organize chores with my housemates from the start.

Write operation (creating a group)  
Persona = new or existing user  

Exception: Duplicate Group Name  
Scenario: A user tries to create a roommate group with a name that already exists.  
Handling: The system will suggest alternative names or require the name to be unique.  

**User Story 6: Editing a Chore**

As a group admin, 
I want to edit an existing chore’s details, so that I can update due dates or fix mistakes.

Write operation (updating a chore)  
Persona = roommate group admin  

Exception: Editing Chore Without Permission  
Scenario: A regular roommate tries to edit a chore they didn’t create.  
Handling: The system will prevent the edit and display a message like: "Only the chore creator or an admin can edit this task."  

**User Story 7: Leaving a Roommate Group**

As a group member,
I want to leave a roommate group, so that I’m no longer responsible for chores in that group if I move out.

Write operation (removing self from group)  
Persona = regular group member  

Exception: User Tries to Leave Administered Group  
Scenario: An admin tries to leave the group when they are the admin.  
Handling: The system will prompt them to assign a new admin before proceeding.  

**User Story 8: Viewing All Group Chores**

As a group member,
I want to view the complete list of all chores in the group, so that I can see what everyone is responsible for and avoid overlap.

Read operation (retrieving group chore list)  
Persona = roommate group member  

Exception: No Chores Exist Yet  
Scenario: The group is newly created and no chores have been added.  
Handling: The system will display a message like: “No chores have been added yet. Check back later.”  

**User Story 9: Assigning Recurring Chores**

As a group admin,
I want to create chores that repeat weekly or monthly, so that I don’t have to manually recreate them every time.

Write operation (creating recurring chores)  
Persona = roommate group admin  

Exception: Invalid Recurrence Pattern  
Scenario: The admin enters a custom recurrence pattern that isn't supported (ex: every 3 days).  
Handling: The system will show an error message like: “Invalid recurrence setting. Please choose from: daily, weekly, or monthly.”  

**User Story 10: Sending Chore Reminders**

As a forgetful roommate,
I want to receive reminders for upcoming chores, so that I don’t miss my responsibilities.

Read operation (reading from chores list)  
Persona = busy student who is forgetful  

Exception: Notifications Disabled  
Scenario: A user has disabled notifications and doesn’t receive reminders.  
Handling: The system will log that reminders were skipped and show a message such as:
 “Reminders are turned off in your settings. Tap here to enable them.”  

**User Story 11: Viewing Chore Completion Stats**

As a responsible roommate,
I want to see how many chores each member has completed, so that I can track group contribution and encourage fairness.

Read operation (gathering chore data)  
Persona = responsible roommate who is on top of things  

Exception: No Completed Chores Yet  
Scenario: A user opens the stats page before any chores have been marked complete.  
Handling: The system will show a message like: “No completed chores yet. Once chores are marked done, your team’s stats will appear here.”  

**User Story 12: Removing a Group Member**

As a group admin,
I want to remove a member from the group, so that chores aren’t assigned to someone who no longer lives with us and has not removed themselves from the group.

Write operation (removing user)  
Persona = roommate group admin  

Exception: Trying to Remove Self  
Scenario: An admin attempts to remove themselves from the group without reassigning the admin role to another user.  
Handling: The system will prompt them to assign a new admin before proceeding.  
