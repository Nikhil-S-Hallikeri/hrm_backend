class LeadActivityLogView(APIView):
    def get(self, request, activity_id):
        try:
            reference_activity = NewDailyAchivesModel.objects.filter(pk=activity_id).first()
            
            if not reference_activity:
                return Response({"error": "Activity not found"}, status=status.HTTP_404_NOT_FOUND)

            phone = reference_activity.candidate_phone or reference_activity.client_phone
            
            if not phone:
                return Response({"error": "No phone number associated with this lead to track history."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch all activities with this phone number
            # We want both candidate and client logs if they match the phone (in case a candidate becomes a client contact or vice versa, though rare. Safer to stick to context).
            
            # Helper to serialize simple fields
            def serialize_log(log):
                return {
                    "id": log.id,
                    "created_date": log.Created_Date,
                    "activity_name": log.current_day_activity.Activity_instance.Activity.activity_name if log.current_day_activity and log.current_day_activity.Activity_instance else "Unknown",
                    "status": log.lead_status or log.client_status or log.interview_status or "Active",
                    "sub_status": log.rejection_type or log.choice, # For rejection details
                    "notes": log.notes or log.client_call_remarks or log.interview_call_remarks or log.job_post_remarks or log.closure_reason,
                    "expected_date": log.expected_date, # For follow ups
                    "expected_time": log.expected_time,
                    "employee_name": log.current_day_activity.Activity_instance.Employee.Name if log.current_day_activity and log.current_day_activity.Activity_instance and log.current_day_activity.Activity_instance.Employee else "Unknown",
                    "lead_name": log.candidate_name or log.client_name,
                    "lead_phone": log.candidate_phone or log.client_phone,
                    "lead_email": log.candidate_email or log.client_email,
                    "company_name": log.client_company_name
                }

            # Query for history
            history_qs = NewDailyAchivesModel.objects.filter(
                Q(candidate_phone=phone) | Q(client_phone=phone)
            ).order_by('-Created_Date') # Newest first

            history_data = [serialize_log(log) for log in history_qs]
            
            # Construct response
            # We can return the "Main" details from the latest log, and then the full list
            latest_log = history_data[0] if history_data else {}
            
            response_data = {
                "lead_details": {
                    "name": latest_log.get("lead_name"),
                    "phone": latest_log.get("lead_phone"),
                    "email": latest_log.get("lead_email"),
                    "company_name": latest_log.get("company_name"),
                    "current_status": latest_log.get("status")
                },
                "history": history_data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
