from django.shortcuts import render
from HRM_App.imports import *
from EMS_App.models import *
from LMS_App.models import *
from LMS_App.serializers import *
from payroll_app.serializer import*


import pandas as pd
import calendar
class DownloadEmployeePaySlipsExcel(APIView):
    def get(self, request,month, year):
        """
        Generates an Excel report for employee pay slips for a given year, month-wise.
        The report contains fields like Employee ID, Name, Designation, Department, etc.
        """
        # Fetch data for the given year
        payslips = EmployeePaySlips.objects.filter(year=year, month=month).order_by('employee__Name')

        # Check if records exist
        if not payslips.exists():
            return HttpResponse("No records found for the given year.", status=404)

        # Define column headers
        columns = [
            "Employee ID", "Name", "Designation", "Department", "No. of Working Days(in month)",
            "No. of Days Worked","on.of leaves taken", "Paid Leaves", "LOPs", "Week of Days","Public/Holidays","Annual CTC", "Monthly Gross",
            "Total Deductions", "Net Pay", "Month","year"
        ]

        # Prepare data
        data = []
        for payslip in payslips:
            data.append([
                payslip.employee.EmployeeId if payslip.employee else "",  # Employee ID
                payslip.employee_name,                                     # Employee Name
                payslip.designation,                                       # Designation
                payslip.employee.Position.Department.Dep_Name if payslip.employee and payslip.employee.Position else "",  # Department
                payslip.total_working_days,                                # No. of Working Days
                payslip.worked_days,                                       # No. of Days Worked
                payslip.leaves_taken, 
                payslip.paid_days,                                         # Paid Leaves
                payslip.lop_days,                                          # LOPs
                payslip.week_off_days,
                payslip.public_holidays,
                payslip.salary,                                            # Annual CTC
                payslip.monthly_gross_pay,                                 # Monthly Gross
                payslip.total_deductions,                                  # Total Deductions
                payslip.net_salary,                                        # Net Pay
                calendar.month_abbr[int(payslip.month)],
                payslip.year                                              # Month
            ])

        # Create a Pandas DataFrame
        df = pd.DataFrame(data, columns=columns)

        # Create an Excel file
        file_name = f"Employee_PaySlips_{month}/{year}.xlsx"
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={file_name}'

        # Save DataFrame to Excel
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name=f"PaySlips_{year}", index=False)

        return response



# Create your views here.
class AllowanceTemplatesCreating(APIView):
    def get(self, request):
        try:
            allowance_type=request.GET.get("type")
            allowance_instance=request.GET.get("id")
            if allowance_type:
                allowance_templates = AllowanceType.objects.filter(type=allowance_type)
                serializer = AllowanceTypeSerializer(allowance_templates, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)
            elif allowance_instance:
                allowance_templates = AllowanceType.objects.filter(pk=allowance_instance).first()
                serializer = AllowanceTypeSerializer(allowance_templates)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                active_allowance={}
                status_map = {
                    'earnings': 'earning_status',
                    'post_tax_deduction': 'post_tax_d_status',
                    'pre_tax_deduction': 'pre_tax_d_status'
                }
                
                for key, status_field in status_map.items():
                    allowances = AllowanceType.objects.filter(**{status_field: True})
                    serializer = AllowanceTypeSerializer(allowances, many=True).data
                    active_allowance[key] = serializer

                return Response(active_allowance, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
    def post(self, request):
        data = request.data.copy()
        serializer = AllowanceTypeSerializer(data=data)
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                print(serializer.errors)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        try:
            obj_pk=request.data.get("id")
            allowance_template = AllowanceType.objects.get(pk=obj_pk)

        except AllowanceType.DoesNotExist:
            return Response({"detail": "Allowance template not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AllowanceTypeSerializer(allowance_template, data=request.data, partial=True)
    
        try:
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request,id):
        try:
            allowance_template = AllowanceType.objects.get(pk=id)
        except AllowanceType.DoesNotExist:
            return Response({"detail": "Allowance template not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"detail": "Invalid ID format."}, status=status.HTTP_400_BAD_REQUEST)
        
        allowance_template.delete()
        return Response({"detail": "Allowance template deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class EmployeesSalaryTemplatesCreating(APIView):
    def get(self,request):
        sal_tem_id=request.GET.get("id")
        if sal_tem_id:
            try:
                sal_tem_id=request.GET.get("id")
                sal_tem_obj=SalaryTemplate.objects.filter(pk=sal_tem_id).first()
                sal_tem_serializer=SalaryTemplatesSerializer(sal_tem_obj).data
                return Response(sal_tem_serializer,status=status.HTTP_200_OK)

            except Exception as e:
                return Response(str(e),status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                sal_tem_obj=SalaryTemplate.objects.all()
                sal_tem_serializer=SalaryTemplatesSerializer(sal_tem_obj,many=True).data
                return Response(sal_tem_serializer,status=status.HTTP_200_OK)
            except Exception as e:
                return Response(str(e),status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request):
        response_data = request.data.copy()
        allowances = response_data.get("allowance_types", [])
        # Serialize SalaryTemplate data
        salary_serializer = SalaryTemplatesSerializer(data=response_data)
        if salary_serializer.is_valid():
            # Save SalaryTemplate instance
            instance = salary_serializer.save()
            # Handle the ManyToMany relationship
            if allowances:
                # Assuming allowances is a list of IDs
                allowance_instances = AllowanceType.objects.filter(id__in=allowances)
                instance.types.set(allowance_instances)
            return Response(salary_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(salary_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def patch(self, request, pk):
        try:
            salary_template = SalaryTemplate.objects.get(pk=pk)
        except SalaryTemplate.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize the serializer with partial update
        serializer = SalaryTemplatesSerializer(salary_template, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Save the changes to the SalaryTemplate instance
            serializer.save()

            # Handle the ManyToManyField separately if 'types' is in the request data
            if 'types' in request.data:
                types_to_add = AllowanceType.objects.filter(id__in=request.data['types'])
                salary_template.types.set(types_to_add)
                salary_template.save()  # Save the updated relationships
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        try:
            salary_template = SalaryTemplate.objects.get(pk=pk)
        except SalaryTemplate.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        salary_template.delete()
        return Response({'detail': 'Deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
    
        
class EmployeeSalaryBreakUpBulkCreateView(APIView):
    def post(self, request):
        data = request.data
        # Ensure data contains 'employees' and 'template'
        if not isinstance(data, dict):
            return Response({"error": "Data must be a dictionary."}, status=status.HTTP_400_BAD_REQUEST)
        employees = data.get('employee_id', [])
        
        template_id = data.get('salary_template')
        
        if not isinstance(employees, list) or not template_id:
            return Response({"error": "Invalid data format. 'employees' should be a list and 'template' should be provided."}, status=status.HTTP_400_BAD_REQUEST)
        # Validate template
        try:
            salary_template = SalaryTemplate.objects.get(pk=template_id)
        except SalaryTemplate.DoesNotExist:
            return Response({"error": "Salary template does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        # Create a list to hold valid instances and errors
        existing_employees = set(EmployeeSalaryBreakUp.objects.values_list('employee_id', flat=True))
        emp_objs=EmployeeDataModel.objects.filter(EmployeeId__in=employees)
        for employee_id in emp_objs:
            if employee_id.pk in existing_employees:
                employee_salary_template=EmployeeSalaryBreakUp.objects.filter(employee_id=employee_id.pk).first()
                allwance_temp=SalaryTemplate.objects.filter(pk=template_id).first()
                employee_salary_template.salary_template=allwance_temp
                employee_salary_template.save()
                continue
            item = {
                'employee_id': employee_id.pk,
                'salary_template': template_id
            }
            serializer = EmployeeSalaryBreakUpSerializer(data=item)
            if serializer.is_valid():
                instance = serializer.save()
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        return Response("success", status=status.HTTP_201_CREATED)
    
    def patch(self,request):
        data=request.data.copy()
        assign_id=data.get("eid")
        data_item={"salary_template":data.get("salary_template")}
        employee_salary_template=EmployeeSalaryBreakUp.objects.filter(employee_id__EmployeeId=assign_id).first()

        serializer = EmployeeSalaryBreakUpSerializer(employee_salary_template,data=data_item,partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            return Response("done!",statue=status.HTTP_200_OK)
        else:
            print(serializer.errors)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        




from django.db.models import Q
from decimal import Decimal

# def generatePaySlip(employee, month, year, total_working_days, total_paid_leaves,total_unpaid_leaves,work_days):
def generatePaySlip(**kwargs): 
    total_working_days = kwargs.get("total_working_days")
    work_days = kwargs.get("work_days")
    week_offs= kwargs.get("week_offs")
    holidays=kwargs.get("holidays")
    total_paid_leaves = kwargs.get("total_paid_leaves")
    total_unpaid_leaves = kwargs.get("total_unpaid_leaves")
    employee = kwargs.get("employee")
    month = kwargs.get("month")
    year = kwargs.get("year")
    
    
    EDO = get_object_or_404(EmployeeDataModel, employeeProfile__employee_Id=employee)
    
    ESB = EmployeeSalaryBreakUp.objects.filter(employee_id=EDO).first()
    gross_salary = Decimal(ESB.CTC_per_annum if ESB else 0)

    monthly_gross_salary=Decimal(gross_salary/12)
    
    if total_working_days == 0:
        daily_gross_salary = Decimal(0)
    else:
        daily_gross_salary = monthly_gross_salary / total_working_days

    #Actual_Working_Days = total_working_days - total_unpaid_leaves

    Actual_Working_Days = (work_days + week_offs + holidays + total_paid_leaves)  #- total_unpaid_leaves
    if employee=="MTM24EMP6E":
        print("Actual_Working_Days",Actual_Working_Days)
        print("work_days + total_paid_leaves",work_days + total_paid_leaves)
        print("total_unpaid_leaves",total_unpaid_leaves)
        
    Salary_for_Actual_Working_Days = daily_gross_salary * Decimal(Actual_Working_Days)

    # Check if payslip already exists
    emp_payslip_obj = EmployeePaySlips.objects.filter(employee__EmployeeId=employee, month=month, year=year).first()

    if not emp_payslip_obj:
        # Create new payslip
        emp_payslip_obj = EmployeePaySlips.objects.create(employee=EDO, salary_breakups=ESB)
        emp_payslip_obj.month = month
        emp_payslip_obj.year = year
        emp_bank_data = BankAccountDetails.objects.filter(EMP_Information__pk=EDO.employeeProfile.pk).first()
        emp_payslip_obj.account_number = emp_bank_data.account_no if emp_bank_data else None
        emp_payslip_obj.bank_branch = emp_bank_data.branch if emp_bank_data else None
        emp_payslip_obj.salary = gross_salary
        emp_payslip_obj.company_name = "Merida Tech Minds"
        emp_payslip_obj.employee_name = EDO.Name
        emp_payslip_obj.designation = EDO.Position.Name if EDO.Position else None
        emp_payslip_obj.total_working_days = total_working_days
        emp_payslip_obj.worked_days = work_days + total_paid_leaves
        emp_payslip_obj.leaves_taken = total_paid_leaves + total_unpaid_leaves
        emp_payslip_obj.lop_days = total_unpaid_leaves
        emp_payslip_obj.paid_days = total_paid_leaves
        emp_payslip_obj.doj = EDO.employeeProfile.hired_date
        emp_payslip_obj.week_off_days=week_offs
        emp_payslip_obj.public_holidays=holidays
        
        #salary_temp = emp_payslip_obj.salary_breakups.salary_template
        salary_temp = emp_payslip_obj.salary_breakups.salary_template if emp_payslip_obj.salary_breakups else None
        #allowance_types = salary_temp.types.all()
        allowance_types = salary_temp.types.all() if salary_temp else None
        allowance_types_list = list(allowance_types if allowance_types else [])
        #allowance_types_list = list(allowance_types)

        total_earning = 0
        total_deductions = 0

        for allowance_type in allowance_types_list:
            allowance_obj = AllowanceType.objects.filter(pk=allowance_type.pk).first()
            if allowance_obj.type == "Earning":
                if allowance_obj.caluculate_type == "Flat_Amount":
                    
                    total_earning += Decimal(allowance_obj.fixed_amount)
                elif allowance_obj.caluculate_type == "Percentage_oF_CTC":
                    amount = (Decimal(allowance_obj.percentage_of_ctc) / 100) * (emp_payslip_obj.salary_breakups.CTC_per_annum / 12)
                    total_earning += amount
            else:
                if allowance_obj.caluculate_type == "Flat_Amount":
                    total_deductions += Decimal(allowance_obj.fixed_amount)
                elif allowance_obj.caluculate_type == "Percentage_oF_CTC":
                    amount = (Decimal(allowance_obj.percentage_of_ctc) / 100) * (emp_payslip_obj.salary_breakups.CTC_per_annum / 12)
                    total_deductions += amount
        
        emp_payslip_obj.monthly_gross_pay = monthly_gross_salary

        emp_payslip_obj.total_deductions =  Decimal(total_deductions) + (Decimal(total_unpaid_leaves) * daily_gross_salary) if work_days > Decimal(0) else Decimal(0)
        emp_payslip_obj.total_earnings = total_earning if work_days > Decimal(0) else Decimal(0)

        emp_payslip_obj.net_salary = Salary_for_Actual_Working_Days - (total_deductions + Decimal(total_paid_leaves))
        

        if emp_payslip_obj.net_salary < 0:
            emp_payslip_obj.net_salary = Decimal(0)

        emp_payslip_obj.save()
    
    # Return the payslip data, whether newly created or existing
    PaySlip_serializer = EmployeePaySlipsSerializer(emp_payslip_obj).data
    #PaySlip_serializer["LOP_amount"]= total_paid_leaves * daily_gross_salary
    return PaySlip_serializer

            
def getEmployeesAttendanceCalculation(emp_id, month, year):
    try:
        cad_obj = CompanyAttendanceDataModel.objects.filter(Emp_Id__EmployeeId=emp_id, date__month=month, date__year=year).exclude(Status__isnull=True)
        cld_obj = EmployeesLeavesmodel.objects.filter(leave_request__employee__EmployeeId=emp_id, leave_date__month=month, leave_date__year=year)

        paid_leaves = cld_obj.filter(fall_under="Paid_Leave").count()

        #full_work_days = cad_obj.filter(Q(Status="present") | Q(Status="week_off") ).count()# | Q(Status="public_leave")
        full_work_days = cad_obj.filter(Q(Status="present")).count()
        week_offs=cad_obj.filter(Status="week_off").count()
        holidays=cad_obj.filter(Status="public_leave").count()
        
        half_days=cad_obj.filter(Status="half_day").count()

        less_than_half_days = cad_obj.filter(Status="less_than_half_day").count()

        unpaid_leaves = cld_obj.filter(fall_under="Unpaid_Leave").count()
        un_info_obj = cad_obj.filter(leave_information="Unauthorized_Absent").count()

        # work_days = full_work_days + (half_days // 2) + (half_days % 2) * 0.5 

        work_days = (
            full_work_days + 
            (half_days // 2) + (half_days % 2) * 0.5 + 
            (less_than_half_days // 4) + (less_than_half_days % 4) * 0.25
        )

        # work_days = full_work_days + (half_days // 2) 

        total_working_days = cad_obj.count()
        total_paid_leaves = paid_leaves
        total_unpaid_leaves = unpaid_leaves + un_info_obj

        # total_unpaid_leaves = total_unpaid_leaves + (half_days//2)

        
        if half_days > 0:
            total_unpaid_leaves += half_days * 0.5

        if less_than_half_days > 0:
            total_unpaid_leaves += less_than_half_days * 0.75

        # if half_days > 2:
        #     total_unpaid_leaves = total_unpaid_leaves + ((half_days-2)/2)
        #     total_paid_leaves=total_paid_leaves + 2
        # else:
        #     total_paid_leaves=total_paid_leaves + (half_days / 2)
           
        att_dict = {
            "total_working_days": total_working_days,
            "work_days": work_days,
            "total_paid_leaves": total_paid_leaves,
            "total_unpaid_leaves": total_unpaid_leaves,
            "week_offs": week_offs,
            "holidays":holidays,
        }
        if emp_id=="MTM24EMP6E":
            print(att_dict)
        return att_dict
    except Exception as e:
        print(e)
        return {}
 
class EmployeesForPaySlip(APIView):
    def post(self, request, month, year, emp_id=None):
        employees = []
        
        if emp_id:
            employee = EmployeeDataModel.objects.filter(employeeProfile__employee_Id=emp_id).exclude(Q(employeeProfile__employee_status='in_active') | Q(employeeProfile__employee_status=None) ).first()
            if employee:
                employees.append(employee)
            else:
                return Response("Employee Not Found", status=status.HTTP_400_BAD_REQUEST)
        else:
            active_employees = EmployeeDataModel.objects.all().exclude(Q(employeeProfile__employee_status='in_active') | Q(employeeProfile__employee_status=None))
            
            
        employees = EmployeeSalaryBreakUp.objects.filter(
                                          employee_id__in=active_employees,  # Filter employees from active ones
                                          salary_template__isnull=False,     # Ensure salary_template is not null
                                          CTC_per_annum__isnull=False        # Ensure CTC_per_annum is not null
                                      )	
  
        payslips = []
        
        for employee in employees:
            
            output = getEmployeesAttendanceCalculation(employee.employee_id.EmployeeId, month, year)
            output["employee"] = employee.employee_id.EmployeeId
            output["month"] = month
            output["year"] = year
            
            employeePayslip = generatePaySlip(**output)
            payslips.append(employeePayslip)
        
        return Response(payslips, status=status.HTTP_200_OK)
    
    def get(self,request,month, year,emp_id=None):
        try:
            if emp_id:
                pay_slip=EmployeePaySlips.objects.filter(month=month,year=year,employee__EmployeeId=emp_id).exclude(employee__employeeProfile__Employeement_Type="intern").first()
                if pay_slip:
                    pay_slip_serializer=EmployeePaySlipsSerializer(pay_slip).data
                    return Response(pay_slip_serializer,status=status.HTTP_200_OK)
                else:
                    return Response(f"No payslip for this EmployeeId on the date:{month}/{year}",status=status.HTTP_400_BAD_REQUEST)
            else:
                pay_slip=EmployeePaySlips.objects.filter(month=month,year=year).exclude(employee__employeeProfile__Employeement_Type="intern").order_by("employee__Name")
                pay_slip_serializer=EmployeePaySlipsSerializer(pay_slip,many=True).data
                return Response(pay_slip_serializer,status=status.HTTP_200_OK)
                
                #if pay_slip.exists():
                    #pay_slip_serializer=EmployeePaySlipsSerializer(pay_slip,many=True).data
                    #return Response(pay_slip_serializer,status=status.HTTP_200_OK)
                #else:
                    #return Response(f"No payslips on the date:{month}/{year}",status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(str(e),status=status.HTTP_400_BAD_REQUEST)