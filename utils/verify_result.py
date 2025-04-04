def get_full_result_data(school, session, term, branch, class_ids, students, request=None):
    from results.models import (
        StudentFinalResult, StudentAverageResult,
        ResultVerificationToken, GradingSystem
    )
    from attendance.models import StudentAttendance, SchoolDaysOpen
    from comments.models import Comment
    from ratings.models import Rating
    from results.views import get_grade_and_remark, get_comment_by_percentage
    from django.db.models import Sum

    grouped_results = {}

    # Fetch totals and helper data
    total_days_open = SchoolDaysOpen.objects.filter(
        branch=branch, session=session, term=term
    ).values_list('days_open', flat=True).first() or 0

    attendance_counts = StudentAttendance.objects.filter(
        session=session, term=term, branch=branch, student__in=students
    ).values("student").annotate(total_attendance=Sum("attendance_count"))

    averages = StudentAverageResult.objects.filter(
        session=session, term=term, branch=branch, student__in=students
    ).select_related("student")

    comments = Comment.objects.filter(
        session=session, term=term, student__in=students
    ).select_related("student", "author")

    results = StudentFinalResult.objects.filter(
        session=session,
        term=term,
        branch=branch,
        student_class__id__in=class_ids,
        student__in=students
    ).select_related("subject", "student").order_by("student__last_name", "subject__name")

    for result in results:
        if result.converted_ca == 0 and result.exam_score == 0:
            continue

        grade, remark = get_grade_and_remark(result.total_score, branch)
        result.grade = grade
        result.remarks = remark
        result.save()

        if result.student_id not in grouped_results:
            attendance = next(
                (item["total_attendance"] for item in attendance_counts if item["student"] == result.student_id), 0
            )
            avg_result = averages.filter(student_id=result.student_id).first()

            average_percentage = (
                round(avg_result.average_percentage, 2)
                if avg_result and avg_result.average_percentage is not None
                else 0
            )

            principal_comment = get_comment_by_percentage(average_percentage)

            profile_picture = (
                result.student.profile_picture.url
                if hasattr(result.student, "profile_picture") and result.student.profile_picture
                else result.student.user.profile_picture.url
                if hasattr(result.student.user, "profile_picture") and result.student.user.profile_picture
                else None
            )

            psychomotor_ratings = Rating.objects.filter(
                student=result.student,
                branch=branch,
                session=session,
                term=term,
                rating_type="psychomotor"
            )

            behavioral_ratings = Rating.objects.filter(
                student=result.student,
                branch=branch,
                session=session,
                term=term,
                rating_type="behavioral"
            )

            token_obj, _ = ResultVerificationToken.objects.get_or_create(
                student=result.student,
                session=session,
                term=term,
                branch=branch,
            )
            # Generate full verification URL
            verification_url = token_obj.get_verification_url(request=request)
            grouped_results[result.student_id] = {
                "first_name": result.student.first_name,
                "last_name": result.student.last_name,
                "gender": result.student.gender.capitalize() if result.student.gender else "N/A",
                "student_id": result.student.student_id or "N/A",
                "profile_picture": profile_picture,
                "class": result.student.student_class.name,
                "attendance_count": attendance,
                "times_absent": max(0, total_days_open - attendance),
                "total_days_school_opened": total_days_open,
                "subjects": [],
                "total_subjects": 0,
                "subjects_failed": 0,
                "subjects_passed": 0,
                "highest_score": None,
                "lowest_score": None,
                "average_score": None,
                "average": {
                    "total_score_obtained": avg_result.total_score_obtained if avg_result else 0,
                    "total_score_maximum": avg_result.total_score_maximum if avg_result else 0,
                    "average_percentage": average_percentage,
                },
                "ratings": {
                    "psychomotor": [rating.to_dict() for rating in psychomotor_ratings],
                    "behavioral": [rating.to_dict() for rating in behavioral_ratings],
                },
                "comments": [
                    {
                        "author": comment.author.get_full_name(),
                        "text": comment.comment_text,
                        "date": comment.created_at
                    }
                    for comment in comments if comment.student_id == result.student_id
                ],
                "principal_comment": principal_comment,
                "verification_token": str(token_obj.token),
                "verification_url": verification_url,
                "max_obtainable_score": 100 * results.filter(student_id=result.student_id).count(),
                "obtained_score": round(
                    results.filter(student_id=result.student_id).aggregate(Sum("total_score"))["total_score__sum"] or 0,
                    2
                ),
            }

        grouped_results[result.student_id]["total_subjects"] += 1
        grouped_results[result.student_id]["subjects"].append({
            "subject": result.subject.name,
            "converted_ca": result.converted_ca,
            "exam_score": result.exam_score,
            "total_score": result.total_score,
            "grade": grade,
            "remark": remark,
            "highest_score": result.highest_score,
            "lowest_score": result.lowest_score,
            "average_score": round(result.average_score, 2) if result.average_score else None
        })

        if grade == "F9":
            grouped_results[result.student_id]["subjects_failed"] += 1
        else:
            grouped_results[result.student_id]["subjects_passed"] += 1

    sorted_students = sorted(
        grouped_results.values(),
        key=lambda x: x["average"]["average_percentage"],
        reverse=True
    )

    return sorted_students
