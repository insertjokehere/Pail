Pail - A Bucket clone
---------------------

	Configuration
	-------------

	Commands
	--------

		Factoids
		--------
		
		*Teaching Factoids*:
			To teach a factoid to Pail, address it in the form
			
			pail: ***trigger* <*mode*> *response***
			
			Where **trigger** is the phrase that should trigger the factoid
			      **response** is the response that should be used
				  **mode**:
					if **mode** is 'reply' then *response* will simply be used as the response
					if **mode** is 'action' then *response* will be used as an IRC action
					otherwise *trigger*, *mode* and *response* will be concatinated together 
					and used as a response
			
			If response contains a variable name (prefixed with '$') it will be replaced
			If *trigger* is said in conversation, the factoid will be triggered
		
		*Protecting/Unprotecting Factoids*
			**This command requires admin privilages**
			To protect or unprotect as factoid, address pail:
			
			pail: **protect factoid #*factoid_number***
			pail: **unprotect factoid #factoid_number**
			
			where *factoid_number* is the ID number of the factoid
			
			All factoids associated with a trigger can be protected/unprotected in a similar manner:
			
			pail: **protect factoid *factoid_trigger***
			pail: **unprotect factoid *factoid_trigger***
			
		*Deleting Factoids*
			To delete a factoid, address pail in the form:
			
			pail: **forget factoid #*factoid_number***
			
			where *factoid_number* is the ID number of the factoid to be deleted
			
			You can also delete all factoids associated with a trigger thus:
			
			pail: **forget factoid *factoid_trigger***
			[**This requires admin privilages**]