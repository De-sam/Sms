@transaction.atomic
def save_student_scores(request, short_code):
    """
    Save or update student scores, calculate class-based highest, lowest, and average scores,
    and update student averages.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            session_id = data.get("session")
            term_id = data.get("term")
            branch_id = data.get("branch")
            subject_id = data.get("subject")
            scores = data.get("scores", [])

            # Validate required fields
            if not session_id or not term_id or not branch_id or not subject_id:
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Fetch related objects
            session = Session.objects.get(id=session_id)
            term = Term.objects.get(id=term_id)
            branch = Branch.objects.get(id=branch_id)
            subject = Subject.objects.get(id=subject_id)

            # Process scores and save/update results
            for score in scores:
                student = Student.objects.get(id=score["student_id"])
                student_class = student.student_class  # Fetch the class directly from the student

                if not student_class:
                    return JsonResponse({
                        "error": f"Student {student.id} does not have an associated class."
                    }, status=400)

                total_score = score["converted_ca"] + score["exam_score"]

                # Save or update final results
                StudentFinalResult.objects.update_or_create(
                    student=student,
                    session=session,
                    term=term,
                    branch=branch,
                    student_class=student_class,
                    subject=subject,
                    defaults={
                        "converted_ca": score["converted_ca"],
                        "exam_score": score["exam_score"],
                        "total_score": total_score,
                        "grade": calculate_grade(total_score),
                        "remarks": generate_remark(calculate_grade(total_score)),
                    },
                )

            # Update highest, lowest, and average scores for each class
            classes = Student.objects.filter(
                final_results__session=session,
                final_results__term=term,
                final_results__branch=branch
            ).values_list('student_class', flat=True).distinct()

            for cls in classes:
                update_class_scores(session, term, branch, cls, subject)

            return JsonResponse({"success": True, "message": "Scores saved successfully."})

        except Exception as e:
            return JsonResponse({"error": f"Error: {str(e)}"}, status=500)


def update_class_scores(session, term, branch, student_class, subject):
    """
    Update the highest, lowest (ignoring zero), and average scores for a given class.
    """
    results = StudentFinalResult.objects.filter(
        session=session,
        term=term,
        branch=branch,
        student_class=student_class,
        subject=subject,
    )

    # Calculate the highest, lowest (excluding zeros), and average scores
    highest_score = results.aggregate(Max("total_score"))["total_score__max"] or 0
    lowest_score = results.exclude(total_score=0).aggregate(Min("total_score"))["total_score__min"] or 0
    average_score = results.aggregate(Avg("total_score"))["total_score__avg"] or 0

    # Update all final results for the class
    results.update(
        highest_score=highest_score,
        lowest_score=lowest_score,
        average_score=round(average_score, 2) if average_score else 0,
    )

    # Update student averages for the class
    update_student_averages(session, term, branch, student_class)

    


def update_student_averages(session, term, branch, student_class):
    """
    Calculate and save/update average results for students in a given class.
    """
    students = Student.objects.filter(
        final_results__session=session,
        final_results__term=term,
        final_results__branch=branch,
        student_class=student_class,
    ).distinct()

    for student in students:
        student_results = StudentFinalResult.objects.filter(
            student=student,
            session=session,
            term=term,
            branch=branch,
            student_class=student_class,
        )

        # Calculate total scores
        total_score_obtained = student_results.aggregate(total_obtained=Sum("total_score"))["total_obtained"] or 0
        total_subjects = student_results.count()
        total_score_maximum = total_subjects * 100  # Assuming max score per subject is 100

        # Save or update average results
        StudentAverageResult.objects.update_or_create(
            student=student,
            session=session,
            term=term,
            branch=branch,
            defaults={
                "total_score_obtained": total_score_obtained,
                "total_score_maximum": total_score_maximum,
                "average_percentage": (total_score_obtained / total_score_maximum) * 100
                if total_score_maximum > 0
                else 0,
            },
        )


def calculate_grade(total_score):
    """
    Calculate grade based on total score following the A1, B2 standard.
    """
    if total_score >= 75:
        return "A1"  # Excellent
    elif total_score >= 70:
        return "B2"  # Very Good
    elif total_score >= 65:
        return "B3"  # Good
    elif total_score >= 60:
        return "C4"  # Credit
    elif total_score >= 55:
        return "C5"  # Credit
    elif total_score >= 50:
        return "C6"  # Credit
    elif total_score >= 45:
        return "D7"  # Pass
    elif total_score >= 40:
        return "E8"  # Pass
    else:
        return "F9"  # Fail


def generate_remark(grade):
    """
    Generate a remark based on the grade.
    """
    remarks = {
        "A1": "Excellent",
        "B2": "Very Good",
        "B3": "Good",
        "C4": "Credit",
        "C5": "Credit",
        "C6": "Credit",
        "D7": "Pass",
        "E8": "Pass",
        "F9": "Fail",
    }
    return remarks.get(grade, "No Remark Available")